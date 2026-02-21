# test_csrf 代码库分析

## 1. 项目定位
这个仓库是一个最小化的 **CSRF 攻击演示项目**：

- `site1`：受害站点（Flask）
- `site2`：攻击站点（静态页面）
- `run_test.py`：通过 Playwright 自动化还原攻击流程

核心目标是展示：当站点仅依赖 Cookie 做身份鉴权、且转账接口没有 CSRF 防护时，用户访问恶意页面即可在已登录状态下触发跨站转账。

## 2. 代码结构

- `site1/app.py`
  - 提供 `/accounts/me` 与 `/accounts/transfer` 两个接口
  - 从 `token` Cookie 中读取登录态
  - 未实现 CSRF token 校验、Origin/Referer 校验
- `site1/accounts.py`
  - 内存账户模型与查询函数
  - `prepare_account` 初始化用户与余额
- `site1/tokenlib.py`
  - 用 HMAC 对用户名签名，生成 `username.signature` 形式 token
  - `secret` 硬编码在源码里
- `site2/app.py`
  - 使用 Python `http.server` 提供静态页面（目录中的 `index.html`）
- `run_test.py`
  - 启动两个站点，注入 Alice 的登录 Cookie
  - 打开受害站点与攻击站点，点击恶意按钮后验证余额下降

## 3. 安全分析

### 3.1 已被演示出的漏洞

1. **CSRF 漏洞（高风险）**
   - `/accounts/transfer` 仅依赖 Cookie 鉴权，未对请求来源做任何校验。
   - 恶意站可诱导浏览器向受害站发起 POST，浏览器会自动带上 Cookie。

2. **认证 token 的密钥硬编码（中风险）**
   - `site1/tokenlib.py` 中 `secret = 'supersecret'`。
   - 一旦源码泄漏，攻击者可伪造任意用户名 token。

3. **缺少输入校验与业务保护（中风险）**
   - `amount` 直接 `int()` 转换，异常场景无显式处理。
   - 未限制负数金额、未校验余额是否充足。

4. **Cookie 安全属性缺失（中风险）**
   - 当前代码没有设置 `HttpOnly` / `Secure` / `SameSite`。
   - 在真实环境中会放大会话劫持与 CSRF 风险。

### 3.2 现有测试状况

- `run_test.py` 是一个端到端攻击复现实验，可直观证明漏洞成立。
- `site1/test_app.py` 当前存在明显问题：
  - `from .site1_app import app` 导入路径不匹配；
  - 请求参数里用 `to`，而服务端读取的是 `recipient`。

## 4. 建议修复方案（按优先级）

1. **给转账接口增加 CSRF 防护（最高优先级）**
   - 推荐双重提交 Cookie 或服务端 Session 绑定 CSRF token。
   - 前端表单必须附带 CSRF token，后端严格校验。

2. **校验请求来源（防御加固）**
   - 对敏感 POST 校验 `Origin`（首选）或 `Referer`（兜底）。
   - 仅允许站点自身来源。

3. **完善 Cookie 策略**
   - 设置 `HttpOnly=True`、`Secure=True`（HTTPS 下）、`SameSite=Lax/Strict`。

4. **加强金额与账户逻辑校验**
   - 金额必须为正整数。
   - 余额不足时拒绝转账。
   - 所有异常分支返回一致的错误码与错误体。

5. **移除硬编码密钥**
   - 从环境变量加载 token 密钥。
   - 在不同环境使用不同密钥并定期轮换。

## 5. 结论

该仓库结构简单、目标明确，非常适合作为 CSRF 教学样例。当前实现侧重“复现漏洞”，未包含生产级安全防护。若要转为真实服务示例，建议先完成 CSRF 防护与鉴权/输入校验强化，再补齐可运行的单元测试。
