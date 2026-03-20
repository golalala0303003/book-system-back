class ErrorMsg:
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

class SuccessMsg:
    REGISTER_SUCCESS = "注册成功ciallo"
    LOGIN_SUCCESS = "登录成功"
    GET_USER_INFO_SUCCESS = "获取用户信息成功"
    IMAGE_UPLOAD_SUCCESS = "图片上传成功"
    UPDATE_USER_SUCCESS = "更新用户信息成功"