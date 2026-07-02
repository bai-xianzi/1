# 本文件核心功能：提供Provider接入中心的本地B2C页面模板，用动态JSON Schema生成表单并调用TASK_024E后端接口。
# - 输入：应用启动时生成的CSRF令牌，以及后端返回的Provider卡片、表单Schema和安全状态。
# - 处理：在浏览器中渲染卡片、配置表单、授权确认、只读测试和撤销动作；秘密字段只写入请求，不写入页面状态或本地存储。
# - 输出：UTF-8 HTML字符串；页面不依赖外部CDN、第三方脚本或网络资源。
# - 常量依据：接入中心使用JSON Schema 2020-12和TASK_024C的`x-field-kind`扩展；本地MVP只服务127.0.0.1。
# - 为什么这样写：复用Web标准和现有动态表单合同，先形成可运行纵向样板，未来可替换成成熟前端框架而不改后端领域逻辑。
"""Local provider connection-center HTML page."""

from __future__ import annotations

import json


# 本段代码核心功能：生成只包含安全令牌和静态前端代码的接入中心页面。
# - 输入：随机csrf_token。
# - 处理：使用json.dumps安全编码到JavaScript常量；其余页面不嵌入Provider配置或秘密。
# - 输出：完整HTML文档。
# - 为什么这样写：Provider数据始终从同源API读取，避免页面源代码、浏览器历史或模板日志包含用户配置。
def render_provider_connection_page(csrf_token: str) -> str:
    if not isinstance(csrf_token, str) or not csrf_token:
        raise ValueError("csrf_token must be a non-empty string")
    token_json = json.dumps(csrf_token, ensure_ascii=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WJX 数据接口接入中心</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: Canvas; color: CanvasText; }}
    header {{ padding: 1rem 1.5rem; border-bottom: 1px solid GrayText; }}
    main {{ max-width: 1100px; margin: auto; padding: 1rem; }}
    .notice {{ padding: .8rem; border: 1px solid #777; border-radius: .6rem; margin-bottom: 1rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }}
    .card {{ border: 1px solid #777; border-radius: .7rem; padding: 1rem; }}
    .status {{ font-weight: 700; }}
    button {{ margin: .25rem .25rem .25rem 0; padding: .55rem .8rem; cursor: pointer; }}
    button:disabled {{ cursor: not-allowed; opacity: .55; }}
    dialog {{ width: min(760px, 92vw); max-height: 88vh; overflow: auto; }}
    label {{ display: block; margin: .8rem 0; }}
    input, select {{ width: 100%; box-sizing: border-box; padding: .55rem; }}
    input[type=checkbox] {{ width: auto; }}
    small, .muted {{ color: GrayText; }}
    pre {{ white-space: pre-wrap; word-break: break-word; padding: .7rem; border: 1px solid #777; }}
    .error {{ color: #c62828; }}
    .success {{ color: #2e7d32; }}
  </style>
</head>
<body>
<header>
  <h1>WJX 数据接口接入中心</h1>
  <div class="muted">选择数据源、填写连接信息、保存到Windows安全凭据库，并查看只读测试状态。</div>
</header>
<main>
  <div class="notice">
    <strong>这个页面是干什么的：</strong>
    以后连接 Wind、iFinD、券商SDK或其他官方数据接口时，可以在这里操作，不需要手工改配置文件。
    密钥不会回显，也不会写进Git、普通JSON或报告。
  </div>
  <div id="message" role="status"></div>
  <section id="cards" class="grid" aria-live="polite"></section>
</main>
<dialog id="connection-dialog">
  <form id="connection-form" method="dialog">
    <h2 id="dialog-title">配置连接</h2>
    <div id="form-fields"></div>
    <fieldset>
      <legend>授权与安全确认</legend>
      <label><input id="authorization" type="checkbox"> 我确认已经通过官方渠道获得合法授权。</label>
      <label><input id="read-only" type="checkbox"> 我确认当前只使用只读行情或研究能力。</label>
      <label><input id="isolated" type="checkbox"> 我确认交易能力保持隔离且未激活。</label>
    </fieldset>
    <div>
      <button id="save-button" type="button">安全保存</button>
      <button type="button" onclick="document.getElementById('connection-dialog').close()">取消</button>
    </div>
  </form>
</dialog>
<script>
// 本段代码核心功能：保存页面运行期的CSRF令牌、当前Provider和表单Schema。
// - 输入：服务端生成的随机令牌和后续API响应。
// - 处理：只存内存变量，不写localStorage、sessionStorage、cookie或URL。
// - 输出：供保存、测试和撤销请求使用。
// - 为什么这样写：页面刷新即销毁令牌和表单状态，降低本地浏览器残留风险。
const CSRF_TOKEN = {token_json};
let currentProviderId = null;
let currentSchema = null;

// 本段代码核心功能：调用同源JSON API并统一处理错误。
// - 输入：路径和fetch选项。
// - 处理：为变更请求添加CSRF头，解析JSON并将后端安全错误转成普通Error。
// - 输出：成功响应对象。
// - 为什么这样写：所有页面动作共享安全请求逻辑，不在各按钮中重复遗漏令牌或错误处理。
async function api(path, options = {{}}) {{
  const request = {{...options, headers: {{...(options.headers || {{}})}}}};
  if (request.method && request.method !== 'GET') {{
    request.headers['X-WJX-CSRF-Token'] = CSRF_TOKEN;
  }}
  const response = await fetch(path, request);
  const payload = await response.json();
  if (!response.ok || payload.ok === false) {{
    throw new Error(payload.error?.message || '请求未完成');
  }}
  return payload;
}}

// 本段代码核心功能：在页面顶部显示成功或失败消息。
// - 输入：文本和错误标志。
// - 处理：仅使用textContent，禁止把后端文本作为HTML插入。
// - 输出：可访问的状态提示。
// - 为什么这样写：textContent可阻断Provider名称或错误消息中的脚本注入。
function showMessage(text, isError = false) {{
  const node = document.getElementById('message');
  node.textContent = text;
  node.className = isError ? 'error' : 'success';
}}

// 本段代码核心功能：加载并渲染全部Provider卡片。
// - 输入：GET /api/provider-connections。
// - 处理：清空旧卡片，使用DOM API创建文字和按钮，按动作可用性禁用未实现功能。
// - 输出：可点击的接入中心首页。
// - 为什么这样写：不使用innerHTML拼接外部字段，防止配置目录内容成为XSS载体。
async function loadCards() {{
  const payload = await api('/api/provider-connections');
  const root = document.getElementById('cards');
  root.replaceChildren();
  for (const card of payload.cards) {{
    const article = document.createElement('article');
    article.className = 'card';
    const title = document.createElement('h2');
    title.textContent = card.display_name;
    const meta = document.createElement('div');
    meta.textContent = `${{card.provider_kind}} · ${{card.authority_tier}}`;
    const status = document.createElement('p');
    status.className = 'status';
    status.textContent = `状态：${{card.status}}`;
    const execution = document.createElement('p');
    execution.textContent = '交易能力：BLOCKED';
    const controls = document.createElement('div');

    const configure = document.createElement('button');
    configure.textContent = '配置连接';
    configure.disabled = !card.action_availability?.OPEN_CONNECTION_FORM?.available;
    configure.addEventListener('click', () => openForm(card.provider_id));
    controls.appendChild(configure);

    const test = document.createElement('button');
    test.textContent = '只读测试';
    test.disabled = !card.action_availability?.RUN_READ_ONLY_CONNECTION_TEST?.available;
    test.title = card.action_availability?.RUN_READ_ONLY_CONNECTION_TEST?.reason || '';
    test.addEventListener('click', () => runTest(card.provider_id));
    controls.appendChild(test);

    const disable = document.createElement('button');
    disable.textContent = '停用并删除凭据';
    disable.disabled = !card.action_availability?.DISABLE_CONNECTION?.available;
    disable.addEventListener('click', () => disableConnection(card.provider_id));
    controls.appendChild(disable);

    article.append(title, meta, status, execution, controls);
    root.appendChild(article);
  }}
}}

// 本段代码核心功能：根据后端JSON Schema生成连接表单。
// - 输入：Provider表单接口返回的schema和安全profile。
// - 处理：为布尔、选择、秘密和普通文本创建对应控件；公开旧值可回填，秘密字段永不回填。
// - 输出：打开的配置对话框。
// - 为什么这样写：同一Schema驱动前后端，新增官方字段无需手改页面，但秘密不会因“编辑模式”被读取。
async function openForm(providerId) {{
  try {{
    const payload = await api(`/api/provider-connections/${{encodeURIComponent(providerId)}}/form`);
    currentProviderId = providerId;
    currentSchema = payload.schema;
    document.getElementById('dialog-title').textContent = payload.provider.display_name;
    const container = document.getElementById('form-fields');
    container.replaceChildren();

    const connectionLabel = document.createElement('label');
    connectionLabel.textContent = '连接标识';
    const connectionInput = document.createElement('input');
    connectionInput.id = 'connection-id';
    connectionInput.required = true;
    connectionInput.pattern = '[a-z][a-z0-9_]{{1,63}}';
    connectionInput.value = payload.profile?.connection_id || `${{providerId}}_default`;
    connectionLabel.appendChild(connectionInput);
    container.appendChild(connectionLabel);

    for (const [fieldId, spec] of Object.entries(payload.schema.properties || {{}})) {{
      const label = document.createElement('label');
      label.textContent = spec.title || fieldId;
      let input;
      if (spec.type === 'boolean') {{
        input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = Boolean(payload.profile?.public_configuration?.[fieldId]);
      }} else if (Array.isArray(spec.enum)) {{
        input = document.createElement('select');
        for (const value of spec.enum) {{
          const option = document.createElement('option');
          option.value = value;
          option.textContent = value;
          input.appendChild(option);
        }}
        input.value = payload.profile?.public_configuration?.[fieldId] || spec.enum[0];
      }} else {{
        input = document.createElement('input');
        input.type = spec['x-field-kind'] === 'secret' ? 'password' : 'text';
        input.autocomplete = spec['x-field-kind'] === 'secret' ? 'new-password' : 'off';
        input.placeholder = spec['x-placeholder'] || '';
        if (spec['x-field-kind'] !== 'secret') {{
          input.value = payload.profile?.public_configuration?.[fieldId] || '';
        }}
      }}
      input.dataset.fieldId = fieldId;
      input.dataset.fieldKind = spec['x-field-kind'] || '';
      input.required = (payload.schema.required || []).includes(fieldId);
      if (spec.pattern) input.pattern = spec.pattern;
      label.appendChild(input);
      if (spec.description) {{
        const help = document.createElement('small');
        help.textContent = spec.description;
        label.appendChild(help);
      }}
      container.appendChild(label);
    }}
    document.getElementById('authorization').checked = Boolean(payload.profile?.official_authorization_confirmed);
    document.getElementById('read-only').checked = Boolean(payload.profile?.read_only_entitlement_confirmed);
    document.getElementById('isolated').checked = Boolean(payload.profile?.execution_domain_isolated);
    document.getElementById('connection-dialog').showModal();
  }} catch (error) {{
    showMessage(error.message, true);
  }}
}}

// 本段代码核心功能：收集动态表单并通过同一次JSON请求安全保存。
// - 输入：当前对话框控件值和三项授权确认。
// - 处理：秘密值只进入局部对象和fetch请求；请求完成后立即关闭并重新加载卡片。
// - 输出：安全档案状态，不在页面显示秘密原文。
// - 为什么这样写：秘密不能先保存到浏览器本地状态或分两次提交，后端才能在同一请求边界交换成Windows凭据引用。
async function saveConnection() {{
  try {{
    const values = {{}};
    for (const input of document.querySelectorAll('#form-fields [data-field-id]')) {{
      const fieldId = input.dataset.fieldId;
      values[fieldId] = input.type === 'checkbox' ? input.checked : input.value;
    }}
    await api(`/api/provider-connections/${{encodeURIComponent(currentProviderId)}}`, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        connection_id: document.getElementById('connection-id').value,
        values,
        official_authorization_confirmed: document.getElementById('authorization').checked,
        read_only_entitlement_confirmed: document.getElementById('read-only').checked,
        execution_domain_isolated: document.getElementById('isolated').checked
      }})
    }});
    document.getElementById('connection-dialog').close();
    showMessage('连接信息已安全保存。');
    await loadCards();
  }} catch (error) {{
    showMessage(error.message, true);
  }}
}}

// 本段代码核心功能：触发已注册Provider的只读连接测试。
// - 输入：providerId。
// - 处理：调用测试接口，不上传新秘密，不启用交易能力。
// - 输出：用户可读测试摘要并刷新状态。
// - 为什么这样写：测试与保存分离，避免页面为每次测试重复发送或暴露密钥。
async function runTest(providerId) {{
  try {{
    const payload = await api(`/api/provider-connections/${{encodeURIComponent(providerId)}}/test`, {{method: 'POST'}});
    showMessage(payload.test_result.summary, !payload.test_result.success);
    await loadCards();
  }} catch (error) {{
    showMessage(error.message, true);
  }}
}}

// 本段代码核心功能：在用户明确确认后删除Windows秘密和无秘密连接档案。
// - 输入：providerId。
// - 处理：浏览器确认后发送DELETE，成功再刷新卡片。
// - 输出：恢复未配置状态。
// - 为什么这样写：撤销是破坏性动作，必须显式确认且由后端保证凭据与档案一起治理。
async function disableConnection(providerId) {{
  if (!window.confirm('确认停用该连接并删除Windows凭据吗？')) return;
  try {{
    await api(`/api/provider-connections/${{encodeURIComponent(providerId)}}`, {{method: 'DELETE'}});
    showMessage('连接已停用，相关凭据已删除。');
    await loadCards();
  }} catch (error) {{
    showMessage(error.message, true);
  }}
}}

document.getElementById('save-button').addEventListener('click', saveConnection);
loadCards().catch(error => showMessage(error.message, true));
</script>
</body>
</html>"""
