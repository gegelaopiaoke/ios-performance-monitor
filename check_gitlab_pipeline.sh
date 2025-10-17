#!/bin/bash

echo "============================================================"
echo "  GitLab Pipeline 状态检查"
echo "============================================================"
echo ""

PROJECT_URL="gitlab.stardustgod.com/wanyihao/rs_ios"
COMMIT_SHA=$(git rev-parse HEAD)
SHORT_SHA=$(git rev-parse --short HEAD)

echo "📦 项目: $PROJECT_URL"
echo "🔖 提交: $SHORT_SHA ($COMMIT_SHA)"
echo ""

echo "============================================================"
echo "  请访问以下链接查看 Pipeline 状态："
echo "============================================================"
echo ""
echo "🔗 Pipelines 列表:"
echo "   https://$PROJECT_URL/-/pipelines"
echo ""
echo "🔗 最新 Pipeline (基于最新提交):"
echo "   https://$PROJECT_URL/-/pipelines?ref=main"
echo ""
echo "🔗 提交详情:"
echo "   https://$PROJECT_URL/-/commit/$COMMIT_SHA"
echo ""

echo "============================================================"
echo "  Pipeline 状态说明："
echo "============================================================"
echo ""
echo "🟡 pending  = 等待 Runner 执行"
echo "🔵 running  = 正在构建中"
echo "✅ passed   = 构建成功，可以下载 exe"
echo "❌ failed   = 构建失败，查看日志"
echo "⚠️  stuck    = 没有可用的 Windows Runner"
echo ""

echo "============================================================"
echo "  下载构建产物（构建成功后）："
echo "============================================================"
echo ""
echo "1. 打开 Pipeline 页面"
echo "2. 点击成功的 Pipeline"
echo "3. 点击 Job (build-android 或 build-unified)"
echo "4. 点击右侧的 'Browse' 或 'Download' 按钮"
echo "5. 下载 dist/ 目录下的 exe 文件"
echo ""

echo "============================================================"
echo "  最近的提交记录："
echo "============================================================"
echo ""
git log --oneline --graph -5
echo ""

# 尝试检查是否有 .gitlab-ci.yml
if [ -f ".gitlab-ci.yml" ]; then
    echo "✅ GitLab CI 配置文件存在: .gitlab-ci.yml"
else
    echo "❌ 未找到 GitLab CI 配置文件"
fi

echo ""
echo "============================================================"
echo "💡 提示: 在浏览器中打开上面的链接查看实时构建状态"
echo "============================================================"
