
vc-data-normalizer/
├── nanoagent.yaml       # 插件清单文件
├── contract.py          # 输入输出 Typed Data Class 定义
├── README.md
├── LICENSE
├── pyproject.toml       # 依赖管理 (如 pydantic, price-parser, pycountry 等)
├── uv.lock
├── .gitignore
├── run.sh               # 环境检查与启动脚本
├── src/plugin/          # MCP 服务及具体工具实现
│   ├── __main__.py      # MCP 服务器入口
│   ├── normalizer.py    # 工具具体逻辑 (清洗算法、汇率/金额转换)
│   ├── taxonomy.py      # 标准行业分类树与词典定义
│   └── tools_dev/       # 离线测试 Case 和 Fixtures
├── tests/               # 离线 pytest 测试集
│   ├── fixtures/        # 预设的脏数据样例 JSON
│   ├── test_normalizer.py
│   └── test_cases.py    # 包含 gold.json 及各类异常 case
├── ui/                  # 前端 Web 渲染脚本
│   ├── renderers.js
│   └── renderers.css
├── product/             # 商店/Marketplace 展示信息
│   ├── product.yaml
│   └── icon.svg
└── verifier/            # 确定性验证器 (100% 纯代码逻辑)
    ├── task.py          # 15+ 规则约束性判定
    └── rules.py         # 确切的逻辑与数值断言匹配