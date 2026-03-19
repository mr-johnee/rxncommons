import re

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "r", encoding="utf-8") as f:
    text = f.read()

type_target = """interface ReviewDetail {
  request: {"""
type_replacement = """interface ReviewHistoryItem {
  id: string;
  status: string;
  submitted_at: string;
  reviewed_at?: string;
  result_reason?: string;
  version_num?: number;
}

interface ReviewDetail {
  history?: ReviewHistoryItem[];
  request: {"""

render_target = """      {/* 底部操作区 */}"""
render_replacement = """      {/* 历史处理记录区 */}
      {detail.history && detail.history.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden mb-6">
          <div className="border-b border-slate-200 bg-slate-50/50 px-6 py-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-500" />
            <h2 className="text-lg font-semibold text-slate-800">历史处理记录</h2>
          </div>
          <div className="p-6">
            <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
              {detail.history.map((record, index) => {
                const isLatest = index === 0;
                let statusColor = "bg-slate-100 text-slate-500 border-slate-200";
                let StatusIcon = Clock;
                let statusLabel = "待审核";
                
                if (record.status === 'approved') {
                  statusColor = "bg-green-100 text-green-700 border-green-200";
                  StatusIcon = CheckCircle2;
                  statusLabel = "已通过";
                } else if (record.status === 'rejected') {
                  statusColor = "bg-red-100 text-red-700 border-red-200";
                  StatusIcon = XCircle;
                  statusLabel = "已驳回";
                } else if (record.status === 'revision_required') {
                  statusColor = "bg-orange-100 text-orange-700 border-orange-200";
                  StatusIcon = AlertTriangle;
                  statusLabel = "需修订";
                }

                return (
                  <div key={record.id} className={`relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active`}>
                    <div className={`flex items-center justify-center w-10 h-10 rounded-full border-4 border-white shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow-sm ${statusColor}`}>
                      <StatusIcon className="w-4 h-4" />
                    </div>
                    
                    <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-xl border border-slate-200 bg-white shadow-sm transition-all hover:shadow-md">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border ${statusColor}`}>
                            {statusLabel}
                          </span>
                          {record.version_num && (
                            <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                              V{record.version_num}
                            </span>
                          )}
                        </div>
                        <time className="text-xs text-slate-400 font-medium">
                          {new Date(record.submitted_at).toLocaleDateString('zh-CN')}
                        </time>
                      </div>
                      
                      <div className="text-sm text-slate-600 mt-2">
                        {record.result_reason ? (
                          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-100 italic">
                            <span className="text-slate-400 mr-1">处理意见:</span>
                            {record.result_reason}
                          </div>
                        ) : (
                          <p className="text-slate-400 italic">无处理意见或等待审核中...</p>
                        )}
                        {record.reviewed_at && (
                           <div className="text-xs text-slate-400 mt-2 text-right">
                             处理于 {new Date(record.reviewed_at).toLocaleString('zh-CN')}
                           </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* 底部操作区 */}"""

if type_target in text:
    text = text.replace(type_target, type_replacement)

if render_target in text:
    text = text.replace(render_target, render_replacement)
    
if "Clock," not in text and "Clock " not in text:
    text = text.replace("Clock3,", "Clock3, Clock,")

with open("/home/zy/zhangyi/rxncommons/frontend/src/app/admin/review-requests/[id]/page.tsx", "w", encoding="utf-8") as f:
    f.write(text)
print("Patched detail page")
