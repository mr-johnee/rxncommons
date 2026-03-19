with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "r", encoding="utf-8") as f:
    text = f.read()

target = """    return {
        "request": {"""

replacement = """    history_reqs = db.query(DatasetReviewRequest).filter(DatasetReviewRequest.dataset_id == dataset.id).order_by(DatasetReviewRequest.submitted_at.desc()).all()
    history = []
    for hr in history_reqs:
        history.append({
            "id": str(hr.id),
            "status": hr.status,
            "submitted_at": hr.submitted_at,
            "reviewed_at": hr.reviewed_at,
            "result_reason": _extract_human_review_reason(hr.result_reason),
            "version_num": _extract_requested_version_num(hr)
        })

    return {
        "history": history,
        "request": {"""

if target in text:
    text = text.replace(target, replacement)
    with open("/home/zy/zhangyi/rxncommons/backend/app/api/v1/endpoints/admin.py", "w", encoding="utf-8") as f:
        f.write(text)
    print("Patched get_review_request_detail to include history")
else:
    print("Target not found")
