import re


def extract_summary(rich_text: str, max_length: int = 30) -> str:
    """
    从富文本(HTML)中提取纯文本摘要
    """
    if not rich_text:
        return ""

    # 使用正则去除所有 HTML 标签 (<...>)
    plain_text = re.sub(r'<[^>]+>', '', rich_text)

    # 去除多余的换行符和空格
    plain_text = " ".join(plain_text.split())

    # 截取指定长度，超长则加上省略号
    if len(plain_text) > max_length:
        return plain_text[:max_length] + "..."
    return plain_text