from __future__ import annotations

import pandas as pd

from .cleaner import clean_text

PRIMARY_RULES = [
    (
        "High-risk / Sensitive",
        [
            "salary",
            "performance",
            "legal",
            "compliance",
            "sensitive",
            "privacy",
            "投诉",
            "仲裁",
            "合规",
            "薪资",
            "绩效",
            "敏感",
            "高风险",
            "prompt injection",
            "jailbreak",
        ],
    ),
    (
        "Human Escalation Needed",
        [
            "special case",
            "personal case",
            "人工",
            "人工处理",
            "工单",
            "ticket",
            "support",
            "manager",
            "manual review",
            "升级处理",
            "人工客服",
        ],
    ),
    (
        "Policy / Rule Question",
        [
            "policy",
            "rule",
            "leave",
            "pto",
            "vacation",
            "reimbursement",
            "certificate",
            "attendance",
            "hr policy",
            "制度",
            "政策",
            "规则",
            "请假",
            "报销",
            "证明",
            "考勤",
        ],
    ),
    (
        "Process Question",
        [
            "process",
            "workflow",
            "how to",
            "apply",
            "submit",
            "approval",
            "流程",
            "步骤",
            "怎么",
            "如何",
            "申请",
            "审批",
            "提交",
        ],
    ),
    (
        "System Entry",
        [
            "portal",
            "system",
            "login",
            "entry",
            "where",
            "link",
            "sso",
            "入口",
            "系统",
            "链接",
            "地址",
            "登录",
            "后台",
        ],
    ),
    (
        "Data / Operation Exception",
        [
            "exception",
            "duplicate",
            "field error",
            "validation",
            "abnormal",
            "data mismatch",
            "字段",
            "异常",
            "重复",
            "报错",
            "数据",
            "审批延迟",
            "delay",
        ],
    ),
    (
        "Product Usage Issue",
        [
            "campaign",
            "listing",
            "refund",
            "logistics",
            "live streaming",
            "onboarding",
            "usage",
            "功能",
            "活动",
            "商品",
            "退款",
            "物流",
            "开播",
            "入驻",
            "不会用",
        ],
    ),
    (
        "Knowledge Gap",
        [
            "not covered",
            "knowledge base",
            "faq",
            "unclear",
            "generic",
            "知识库",
            "没覆盖",
            "不清楚",
            "答非所问",
            "模糊",
        ],
    ),
]

SECONDARY_RULES = [
    ("prompt_injection", ["prompt injection", "jailbreak", "ignore previous", "忽略之前指令"]),
    ("leave_request", ["leave", "pto", "vacation", "请假", "休假"]),
    ("reimbursement", ["reimbursement", "expense", "报销", "发票"]),
    ("certificate_request", ["certificate", "证明", "在职证明", "employment letter"]),
    ("system_access", ["system", "portal", "login", "sso", "entry", "入口", "登录"]),
    ("campaign_setup", ["campaign", "promotion", "活动", "campaign setup"]),
    ("merchant_onboarding", ["onboarding", "merchant onboarding", "入驻", "开店"]),
    ("logistics_exception", ["logistics", "shipment", "delivery", "物流", "发货"]),
    ("product_listing", ["listing", "sku", "商品上架", "product listing"]),
    ("refund_after_sales", ["refund", "after-sales", "售后", "退款"]),
    ("unclear_question", ["unclear", "not clear", "模糊", "答非所问"]),
    ("personal_case", ["special case", "personal case", "个人情况", "特殊情况"]),
    ("approval_delay", ["approval delay", "pending approval", "审批延迟", "审批很久"]),
    ("field_error", ["field error", "invalid field", "字段错误", "必填字段"]),
    ("duplicate_modification", ["duplicate", "modify twice", "重复修改", "重复提交"]),
]



def contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)



def classify_feedback(raw_feedback: object) -> tuple[str, str]:
    text = clean_text(raw_feedback).lower()

    primary_issue_category = "Other"
    for category, keywords in PRIMARY_RULES:
        if contains_any(text, keywords):
            primary_issue_category = category
            break

    secondary_tag = "other"
    for tag, keywords in SECONDARY_RULES:
        if contains_any(text, keywords):
            secondary_tag = tag
            break

    return primary_issue_category, secondary_tag



def add_classification_columns(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    classifications = working["cleaned_feedback"].apply(classify_feedback)
    working["primary_issue_category"] = classifications.apply(lambda item: item[0])
    working["secondary_tag"] = classifications.apply(lambda item: item[1])
    return working
