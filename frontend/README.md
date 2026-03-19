# Frontend 启动说明

## 关键要求

- Node.js 必须 >= 20.9.0（Next.js 16 要求）
- 推荐使用 conda 环境 `rxn_front`

## 本地开发启动

```bash
source /home/zy/anaconda3/etc/profile.d/conda.sh
conda activate rxn_front
cd /home/zy/zhangyi/rxncommons/frontend
npm install
npm run dev
```

前端固定监听在 `0.0.0.0:3000`。

## 访问地址

- 本机访问: http://127.0.0.1:3000
- 局域网/远程访问: http://<服务器IP>:3000
