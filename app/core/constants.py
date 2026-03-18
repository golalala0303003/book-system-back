class ErrorMsg:
    USER_ALREADY_EXISTS = "该用户名已被注册，请更换一个"
    INVALID_CREDENTIALS = "用户名或密码错误"
    TOKEN_EXPIRED = "无效的认证凭证或登录已过期"
    USER_NOT_FOUND = "用户不存在或已被删除"
    TOKEN_MISSING = "未提供登录凭证，请先登录"

class SuccessMsg:
    REGISTER_SUCCESS = "注册成功"
    LOGIN_SUCCESS = "登录成功"
    GET_USER_INFO_SUCCESS = "获取用户信息成功"