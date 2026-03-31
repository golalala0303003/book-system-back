import math

class VectorConverter:
    @staticmethod
    def str_to_dict(vector_str: str) -> dict[int, float]:
        """将数据库存储的 '1:0.5,2:0.8' 转换为字典 {1: 0.5, 2: 0.8}"""
        if not vector_str or vector_str.strip() == "":
            return {}
        try:
            return {
                int(k): float(v)
                for k, v in (item.split(':') for item in vector_str.split(',') if ':' in item)
            }
        except ValueError:
            return {}

    @staticmethod
    def dict_to_str(vector_dict: dict[int, float]) -> str:
        """将字典 {1: 0.5, 2: 0.8} 转换为存储字符串 '1:0.5000,2:0.8000'"""
        if not vector_dict:
            return ""
        # 按照索引排序，保证字符串存储的有序性，方便肉眼排查
        sorted_items = sorted(vector_dict.items())
        return ",".join([f"{k}:{v:.4f}" for k, v in sorted_items])

    @staticmethod
    def log_normalize(vector_dict: dict[int, float]) -> dict[int, float]:
        """对用户特征向量进行对数平滑处理：log(1 + x)"""
        return {k: math.log1p(v) for k, v in vector_dict.items()}