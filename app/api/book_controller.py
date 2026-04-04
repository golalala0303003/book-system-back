from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.models.user import User
from app.dependencies import get_current_user_optional, get_current_user
from app.schemas.result import Result
from app.schemas.book_schema import BookQueryDTO, BookVoteDTO, BookFavoriteDTO, BookCreateDTO, BookUpdateDTO, \
    BookDeleteDTO, BookVO
from app.service.book_service import BookService
from app.core.constants import SuccessMsg

book_router = APIRouter(prefix="/book", tags=["图书百科模块"])

@book_router.post("/page")
def get_book_page(
    dto: BookQueryDTO,
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: BookService = Depends()
):
    """通用分页检索图书 (支持多种条件与排序，游客可用)"""
    page_data = service.get_book_page(dto, current_user)
    return Result.success(data=page_data, message=SuccessMsg.GET_BOOK_PAGE_SUCCESS)

@book_router.get("/suggest")
def get_book_suggest(key_word: str, limit: int = 5, service: BookService = Depends()):
    book_suggest_vo = service.get_book_suggest(key_word, limit)
    return Result.success(data=book_suggest_vo, message=SuccessMsg.GET_BOOK_SUGGEST_SUCCESS)

@book_router.get("/detail/{book_id}")
def get_book_detail(
    book_id: int,
    record_view: bool = Query(True, description="是否记录浏览记录和浏览量"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    service: BookService = Depends()
):
    """获取图书详情 (游客可用，附带浏览量+1与历史记录)"""
    book_vo = service.get_book_detail(book_id, record_view, current_user)
    return Result.success(data=book_vo, message=SuccessMsg.GET_BOOK_DETAIL_SUCCESS)

@book_router.get("/tags")
def get_book_tags(service: BookService = Depends()):
    """获取图书高频分类标签 (用于前端导航栏)"""
    tags = service.get_hot_tags()
    return Result.success(data=tags, message=SuccessMsg.GET_BOOK_TAGS_SUCCESS)

@book_router.post("/vote")
def vote_book(
    dto: BookVoteDTO,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends()
):
    """书籍点赞/踩 (支持取消与反转)"""
    service.vote_book(dto, current_user)
    return Result.success(message=SuccessMsg.ACTION_SUCCESS)

@book_router.post("/favorite")
def favorite_book(
    dto: BookFavoriteDTO,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends()
):
    """收藏书籍/修改阅读状态 (支持取消收藏)"""
    service.favorite_book(dto, current_user)
    return Result.success(message=SuccessMsg.ACTION_SUCCESS)

@book_router.post("/create")
def create_book(
    dto: BookCreateDTO,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends()
):
    """人工录入新书 (仅限管理员)"""
    book_vo = service.create_book(dto, current_user)
    return Result.success(data=book_vo, message="书籍录入成功")

@book_router.post("/update")
def update_book(
    dto: BookUpdateDTO,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends()
):
    """修改书籍信息 (仅限管理员，支持部分字段更新)"""
    book_vo = service.update_book(dto, current_user)
    return Result.success(data=book_vo, message="书籍修改成功")

@book_router.post("/delete")
def delete_book(
    dto: BookDeleteDTO,
    current_user: User = Depends(get_current_user),
    service: BookService = Depends()
):
    """下架书籍 (仅限管理员)"""
    service.delete_book(dto.book_id, current_user)
    return Result.success(message="书籍已成功下架")


@book_router.post("/refresh-tags")
def refresh_book_tags(
        current_user: User = Depends(get_current_user),
        service: BookService = Depends()
):
    """
    [管理员工具] 扫描全库书籍标签并更新索引映射表
    用于在导入新书后，确保所有新标签都有对应的向量索引位。
    """
    if current_user.role != "admin":
        return Result.fail(message="只有管理员有权操作此工具")

    result = service.refresh_tag_indices()
    return Result.success(data=result, message="标签索引表更新成功")


@book_router.post("/calculate-tfidf")
def calculate_tfidf_vectors(
        current_user: User = Depends(get_current_user),
        service: BookService = Depends()
):
    """
    [管理员工具] 重新计算并刷新全库书籍的 TF-IDF 权重向量。
    当新增大量图书、或者手动修改过标签字典后，应执行此操作。
    """
    if current_user.role != "admin":
        return Result.fail(message="只有管理员有权执行算法重算")

    try:
        updated_count = service.calculate_all_books_tfidf()
        return Result.success(data={"updated_count": updated_count}, message="TF-IDF 矩阵计算并存储成功！")
    except Exception as e:
        return Result.fail(message=f"计算失败: {str(e)}")

@book_router.get("/recommend", response_model=Result[list[BookVO]])
def get_recommend_books(
    limit: int = 10,
    current_user: User = Depends(get_current_user_optional), # 获取当前登录用户
    service: BookService = Depends()
):
    """
    获取个性化书籍推荐列表 (首页/猜你喜欢)
    """
    recommendations = service.get_personalized_recommendations(current_user, limit)
    return Result.success(data=recommendations)