class ErrorMsg:
    LLM_NOT_AVAILABLE = "大模型目前不可用"
    BOOK_ALREADY_EXISTS = "该书已经存在，请勿重复添加"
    USER_ALREADY_EXISTS = "该用户名已被注册，请更换一个"
    INVALID_CREDENTIALS = "用户名或密码错误"
    TOKEN_EXPIRED = "无效的认证凭证或登录已过期"
    USER_NOT_FOUND = "用户不存在或已被删除"
    TOKEN_MISSING = "未提供登录凭证，请先登录"
    INCORRECT_PASSWORD = "密码错误"
    UPLOAD_FAILED = "文件上传失败，请稍后重试"
    INVALID_FILE_TYPE = "不支持的文件格式"
    FILE_TOO_LARGE = "文件大小超出限制"
    LEAST_ONE_FIELD = "至少要传一个参数来吧"
    BOARD_ALREADY_EXISTS = "板块已存在"
    BOARD_NOT_EXISTS = "板块不存在"
    USER_NOT_PERMITTED = "用户的权限不允许执行该操作"
    POST_NOT_EXISTS = "帖子不存在"
    COMMENT_NOT_EXISTS = "回复的父评论不存在或已被删除"
    INVALID_COMMENT_LEVEL = "parent_id 必须是一级评论的ID"
    BOOK_NOT_EXISTS = "该书不存在"


class SuccessMsg:
    GET_BOARD_SUGGEST_SUCCESS = "获取板块联想成功"
    GET_BOARD_DETAIL_SUCCESS = "获取板块信息成功"
    GET_FAVORITE_BOARD_LIST_SUCCESS = "获取收藏板块成功"
    GET_BOOK_SUGGEST_SUCCESS = "获得书籍联想成功"
    REGISTER_SUCCESS = "注册成功ciallo"
    LOGIN_SUCCESS = "登录成功"
    GET_USER_INFO_SUCCESS = "获取用户信息成功"
    IMAGE_UPLOAD_SUCCESS = "图片上传成功"
    UPDATE_USER_SUCCESS = "更新用户信息成功"
    BOARD_CREATE_SUCCESS = "板块创建成功"
    BOARD_DELETE_SUCCESS = "板块删除/隐藏成功"
    GET_BOARD_LIST_SUCCESS = "获取板块列表成功"
    POST_CREATE_SUCCESS = "帖子创建成功"
    POST_DELETE_SUCCESS = "帖子删除成功"
    GET_POST_DETAIL_SUCCESS = "成功查看帖子记录"
    POST_PAGE_SUCCESS = "成功进行了帖子分页查询"
    POST_UPDATE_SUCCESS = "帖子更新成功"
    COMMENT_CREATE_SUCCESS = "评论成功"
    COMMENT_DELETE_SUCCESS = "评论删除成功"
    GET_COMMENT_LIST_SUCCESS = "获取评论列表成功"
    ACTION_SUCCESS = "操作成功"
    GET_BOOK_PAGE_SUCCESS = "获取图书列表成功"
    GET_BOOK_DETAIL_SUCCESS = "获取图书详情成功"
    GET_BOOK_TAGS_SUCCESS = "获取标签列表成功"


class ActionWeight:
    VIEW = 1.0       # 浏览书籍详情
    UPVOTE = 3.0     # 点赞
    COLLECT = 5.0    # 收藏/正在读
    POST = 4.0       # 为书发帖
    COMMENT = 2.0    # 在书籍相关帖子下评论

class RecommendValue:
    DECAY_CONSTANT = 0.95


class PromptTemplates:
    """
    大模型提示词
    """

    # 图书科普/问答 系统提示词
    BOOK_KNOWLEDGE_SYSTEM_PROMPT = """你是一个专业的图书推荐官和阅读顾问。
当前用户正在浏览以下书籍的详情：
《{title}》
作者：{author}
出版社：{publisher}
出版年：{publish_year}
豆瓣评分：{douban_rating}
标签：{tags}
内容简介：{summary}

请根据以上书籍信息，回答用户的提问。
要求：
1. 结合书籍内容，回答客观、专业、有针对性。
2. 如果用户的提问与该书无关，请委婉地引导回当前图书相关话题。
3. 语言风格自然，排版清晰易读。"""

    @classmethod
    def build_book_system_prompt(cls, book: dict) -> str:
        """
        构建图书专属的系统提示词
        """
        # 使用 safe_dict 处理可能的 None 值，防止格式化报错
        safe_dict = {k: (v if v is not None else "未知") for k, v in book.items()}
        return cls.BOOK_KNOWLEDGE_SYSTEM_PROMPT.format(**safe_dict)