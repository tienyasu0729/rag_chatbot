"""
Build expertExplanation từ dữ liệu đã tính.
"""

from __future__ import annotations


def build_explanation(
    *,
    market_stats: dict,
    pricing_breakdown: dict,
    condition: dict,
    risk_assessment: dict,
    trust_assessment: dict,
    pricing_adjustments: list[dict],
    warnings: list[str],
    fallback: dict,
    result_type: str,
    variant_match_coverage: dict | None = None,
) -> dict:
    variant_match_coverage = variant_match_coverage or {}
    market_reasoning = []
    if market_stats.get("similarListingsUsed"):
        market_reasoning.append(f"Có {market_stats['similarListingsUsed']} tin rao tương tự được sử dụng sau khi lọc dữ liệu.")
    if market_stats.get("medianPrice") is not None:
        market_reasoning.append(f"Giá trung vị thị trường là {market_stats['medianPrice']:,} VND.")
    if market_stats.get("p25Price") is not None and market_stats.get("p75Price") is not None:
        market_reasoning.append(f"Khoảng giá tham chiếu có trọng số nằm trong vùng {market_stats['p25Price']:,} - {market_stats['p75Price']:,} VND.")

    if result_type == "low_data_model_estimate":
        market_reasoning.append("Có dữ liệu cùng model nhưng số lượng tin rao còn ít, kết quả chỉ mang tính tham khảo.")
    elif result_type == "taxonomy_fallback_estimate":
        market_reasoning.append("Giá đang được cứu bằng fallback theo model keyword do taxonomy input có thể lệch.")
    elif result_type == "rough_segment_estimate":
        market_reasoning.append("Kết quả hiện tại chỉ được suy luận theo nhóm xe tương đồng rộng hơn, không phải cùng model chắc chắn.")

    condition_reasoning = [
        f"Tình trạng ảnh tổng thể được đánh giá ở mức {condition['label'].lower()} với car quality score {condition['carQualityScore']}.",
        f"Risk score ở mức {risk_assessment.get('riskScore')} và trust score ở mức {trust_assessment.get('trustScore')}.",
    ]
    if condition.get("visibleDamage"):
        condition_reasoning.append("Ảnh cho thấy có dấu hiệu hao mòn hoặc hư hại nhìn thấy được, cần đưa vào chi phí xử lý sau mua.")
    if warnings:
        condition_reasoning.append("Một số góc ảnh còn thiếu hoặc chỉ bao phủ một phần nên độ chắc chắn chưa tối đa.")

    purchase_reasoning = []
    if pricing_breakdown.get("conditionAdjustment"):
        purchase_reasoning.append("Fair price đã điều chỉnh theo condition tổng thể và trust penalty.")
    if pricing_breakdown.get("estimatedReconditioningCost"):
        purchase_reasoning.append("Purchase price đã trừ chi phí dọn sửa dự kiến, risk buffer và biên lợi nhuận mục tiêu.")
    if result_type == "rough_segment_estimate":
        purchase_reasoning.append("Không trả giá thu vào suggested vì hiện chỉ có dữ liệu segment rộng.")

    exact_variant_matches = int(variant_match_coverage.get("exactVariantMatches") or 0)
    if exact_variant_matches == 0 and variant_match_coverage:
        purchase_reasoning.append("Chưa có đủ dữ liệu đúng phiên bản, giá được suy luận từ candidate cùng dòng hoặc gần phiên bản.")

    limitations = [
        "Kết quả dựa trên giá rao bán thị trường, không phải giá giao dịch sau thương lượng.",
        "Cần kiểm tra thực tế máy, gầm, hộp số và giấy tờ trước khi chốt giá cuối cùng.",
    ]
    if fallback.get("used"):
        limitations.append(fallback["description"])

    recommended = []
    for warning in warnings:
        lowered = warning.lower()
        if "odo" in lowered or "odometer" in lowered:
            recommended.append("Bổ sung ảnh đồng hồ ODO.")
        if "engine_bay" in lowered or "khoang may" in lowered:
            recommended.append("Bổ sung ảnh khoang máy.")
    if result_type in {"rough_segment_estimate", "insufficient_market_data"}:
        recommended.append("Cần chuyên viên định giá kiểm tra thủ công.")

    summary_map = {
        "standard_estimate": "Xe được định giá dựa trên nhóm tin rao tương tự, condition ảnh và pricing policy.",
        "variant_uncertain_estimate": "Kết quả được suy luận dựa trên cùng dòng xe, nhưng độ chắc chắn về phiên bản chưa cao.",
        "low_data_model_estimate": "Đã tìm thấy dữ liệu cùng model, nhưng số lượng listing còn ít nên kết quả chỉ ở mức tham khảo thấp.",
        "taxonomy_fallback_estimate": "Taxonomy input có thể lệch, hệ thống đã fallback theo model keyword để cứu market candidates.",
        "rough_segment_estimate": "Không đủ dữ liệu cùng model chắc chắn, kết quả chỉ là tham khảo theo nhóm xe gần tương đồng.",
        "insufficient_market_data": "Không đủ dữ liệu thị trường để đưa ra kết quả định giá đáng tin cậy.",
    }

    return {
        "summary": summary_map.get(result_type, summary_map["standard_estimate"]),
        "marketReasoning": market_reasoning,
        "conditionReasoning": condition_reasoning,
        "purchaseReasoning": purchase_reasoning,
        "limitations": limitations,
        "recommendedNextActions": list(dict.fromkeys(recommended)),
    }
