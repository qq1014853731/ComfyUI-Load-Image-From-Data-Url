class AnyType(str):
    def __ne__(self, other):
        return False


ANY_TYPE = AnyType("*")


class LazyGateAny:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "enabled": ("BOOLEAN", {"default": True}),
                "value": (ANY_TYPE, {"lazy": True}),
            }
        }

    RETURN_TYPES = (ANY_TYPE,)
    RETURN_NAMES = ("value",)
    FUNCTION = "run"
    CATEGORY = "lifu"

    def check_lazy_status(self, enabled, value=None):
        # enabled 为 True 时，才真正请求 lazy 输入 value
        if enabled and value is None:
            return ["value"]
        return []

    def run(self, enabled, value=None):
        # enabled 为 False：不取上游，直接返回 None
        if not enabled:
            return (None,)

        # enabled 为 True：透传真实值
        return (value,)
