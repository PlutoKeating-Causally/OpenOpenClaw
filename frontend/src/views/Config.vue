<template>
  <div class="config">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>选择配置目标</span>
            </div>
          </template>
          <el-form label-width="80px">
            <el-form-item label="配置类型">
              <el-radio-group v-model="configType">
                <el-radio label="instance">实例配置</el-radio>
                <el-radio label="group">群组配置</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="选择目标" v-if="configType === 'instance'">
              <el-select v-model="selectedTarget" placeholder="选择实例" style="width: 100%;">
                <el-option v-for="i in instances" :key="i.id" :label="`${i.name} (${i.group_name})`" :value="i.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="选择群组" v-else>
              <el-select v-model="selectedTarget" placeholder="选择群组" style="width: 100%;">
                <el-option v-for="g in groups" :key="g.id" :label="g.name" :value="g.id" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="loadConfig">加载配置</el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>BYOK 配置模板</span>
          </template>
          <div class="templates">
            <el-collapse v-model="activeTemplates">
              <el-collapse-item title="OpenAI" name="openai">
                <el-form label-width="160px">
                  <el-form-item label="OPENAI_API_KEY">
                    <el-input v-model="templates.openai.OPENAI_API_KEY" placeholder="sk-xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Anthropic (Claude)" name="anthropic">
                <el-form label-width="160px">
                  <el-form-item label="ANTHROPIC_API_KEY">
                    <el-input v-model="templates.anthropic.ANTHROPIC_API_KEY" placeholder="sk-ant-xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Google AI (Gemini)" name="google">
                <el-form label-width="160px">
                  <el-form-item label="GEMINI_API_KEY">
                    <el-input v-model="templates.google.GEMINI_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Azure OpenAI" name="azure">
                <el-form label-width="160px">
                  <el-form-item label="AZURE_OPENAI_API_KEY">
                    <el-input v-model="templates.azure.AZURE_OPENAI_API_KEY" />
                  </el-form-item>
                  <el-form-item label="AZURE_OPENAI_ENDPOINT">
                    <el-input v-model="templates.azure.AZURE_OPENAI_ENDPOINT" placeholder="https://xxx.openai.azure.com" />
                  </el-form-item>
                  <el-form-item label="AZURE_OPENAI_DEPLOYMENT">
                    <el-input v-model="templates.azure.AZURE_OPENAI_DEPLOYMENT" placeholder="gpt-4o" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="DeepSeek" name="deepseek">
                <el-form label-width="160px">
                  <el-form-item label="DEEPSEEK_API_KEY">
                    <el-input v-model="templates.deepseek.DEEPSEEK_API_KEY" placeholder="sk-xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="MiniMax" name="minimax">
                <el-form label-width="160px">
                  <el-form-item label="MINIMAX_API_KEY">
                    <el-input v-model="templates.minimax.MINIMAX_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Ollama (本地)" name="ollama">
                <el-form label-width="160px">
                  <el-form-item label="OLLAMA_API_KEY">
                    <el-input v-model="templates.ollama.OLLAMA_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="OpenRouter" name="openrouter">
                <el-form label-width="160px">
                  <el-form-item label="OPENROUTER_API_KEY">
                    <el-input v-model="templates.openrouter.OPENROUTER_API_KEY" placeholder="sk-or-xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Hugging Face" name="huggingface">
                <el-form label-width="160px">
                  <el-form-item label="HUGGINGFACE_HUB_TOKEN">
                    <el-input v-model="templates.huggingface.HUGGINGFACE_HUB_TOKEN" placeholder="hf_xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Groq" name="groq">
                <el-form label-width="160px">
                  <el-form-item label="GROQ_API_KEY">
                    <el-input v-model="templates.groq.GROQ_API_KEY" placeholder="gsk_xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="xAI (Grok)" name="xai">
                <el-form label-width="160px">
                  <el-form-item label="XAI_API_KEY">
                    <el-input v-model="templates.xai.XAI_API_KEY" placeholder="xai-xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Cohere" name="cohere">
                <el-form label-width="160px">
                  <el-form-item label="COHERE_API_KEY">
                    <el-input v-model="templates.cohere.COHERE_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Mistral" name="mistral">
                <el-form label-width="160px">
                  <el-form-item label="MISTRAL_API_KEY">
                    <el-input v-model="templates.mistral.MISTRAL_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Voyage AI" name="voyage">
                <el-form label-width="160px">
                  <el-form-item label="VOYAGE_API_KEY">
                    <el-input v-model="templates.voyage.VOYAGE_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Kimi (Moonshot)" name="kimi">
                <el-form label-width="160px">
                  <el-form-item label="KIMI_API_KEY">
                    <el-input v-model="templates.kimi.KIMI_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Venice" name="venice">
                <el-form label-width="160px">
                  <el-form-item label="VENICE_API_KEY">
                    <el-input v-model="templates.venice.VENICE_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Nvidia" name="nvidia">
                <el-form label-width="160px">
                  <el-form-item label="NVIDIA_API_KEY">
                    <el-input v-model="templates.nvidia.NVIDIA_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Synthetic" name="synthetic">
                <el-form label-width="160px">
                  <el-form-item label="SYNTHETIC_API_KEY">
                    <el-input v-model="templates.synthetic.SYNTHETIC_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Kilocode" name="kilocode">
                <el-form label-width="160px">
                  <el-form-item label="KILOCODE_API_KEY">
                    <el-input v-model="templates.kilocode.KILOCODE_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="AI Gateway" name="ai_gateway">
                <el-form label-width="160px">
                  <el-form-item label="AI_GATEWAY_API_KEY">
                    <el-input v-model="templates.ai_gateway.AI_GATEWAY_API_KEY" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
            </el-collapse>
            <div style="margin-top: 10px; display: flex; gap: 10px;">
              <el-button type="primary" @click="applyTemplates" style="flex: 1;">
                应用模板
              </el-button>
              <el-button type="success" @click="saveTemplatesToServer" style="flex: 1;">
                保存模板
              </el-button>
              <el-button @click="loadTemplates">
                加载模板
              </el-button>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 20px;">
          <template #header>
            <span>渠道配置模板</span>
          </template>
          <div class="templates">
            <el-collapse v-model="activeChannelTemplates">
              <el-collapse-item title="Telegram" name="telegram">
                <el-form label-width="160px">
                  <el-form-item label="TELEGRAM_BOT_TOKEN">
                    <el-input v-model="channelTemplates.telegram.TELEGRAM_BOT_TOKEN" placeholder="123456:ABC-DEF" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Discord" name="discord">
                <el-form label-width="160px">
                  <el-form-item label="DISCORD_BOT_TOKEN">
                    <el-input v-model="channelTemplates.discord.DISCORD_BOT_TOKEN" placeholder="xxx" />
                  </el-form-item>
                  <el-form-item label="DISCORD_GUILD_ID">
                    <el-input v-model="channelTemplates.discord.DISCORD_GUILD_ID" placeholder="xxx" />
                  </el-form-item>
                  <el-form-item label="DISCORD_USER_ID">
                    <el-input v-model="channelTemplates.discord.DISCORD_USER_ID" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="飞书 (Feishu)" name="feishu">
                <el-form label-width="160px">
                  <el-form-item label="FEISHU_APP_ID">
                    <el-input v-model="channelTemplates.feishu.FEISHU_APP_ID" placeholder="cli_xxx" />
                  </el-form-item>
                  <el-form-item label="FEISHU_APP_SECRET">
                    <el-input v-model="channelTemplates.feishu.FEISHU_APP_SECRET" placeholder="xxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="WhatsApp" name="whatsapp">
                <el-form label-width="160px">
                  <el-form-item label="WHATSAPP_SESSION_PATH">
                    <el-input v-model="channelTemplates.whatsapp.WHATSAPP_SESSION_PATH" placeholder="/root/.openclaw/credentials/whatsapp" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Slack" name="slack">
                <el-form label-width="160px">
                  <el-form-item label="SLACK_BOT_TOKEN">
                    <el-input v-model="channelTemplates.slack.SLACK_BOT_TOKEN" placeholder="xoxb-xxx" />
                  </el-form-item>
                  <el-form-item label="SLACK_TEAM_ID">
                    <el-input v-model="channelTemplates.slack.SLACK_TEAM_ID" placeholder="Txxx" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
              <el-collapse-item title="Signal" name="signal">
                <el-form label-width="160px">
                  <el-form-item label="SIGNAL电话号码">
                    <el-input v-model="channelTemplates.signal['SIGNAL电话号码']" placeholder="+1234567890" />
                  </el-form-item>
                </el-form>
              </el-collapse-item>
            </el-collapse>
            <div style="margin-top: 10px;">
              <el-button type="primary" @click="applyChannelTemplates" style="width: 100%;">
                应用渠道配置
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>配置编辑</span>
              <el-button type="primary" @click="saveConfig" :disabled="!selectedTarget">
                <el-icon><Check /></el-icon>
                保存配置
              </el-button>
            </div>
          </template>

          <el-tabs v-model="activeTab">
            <el-tab-pane label="环境变量 (.env)" name="env">
              <el-form label-width="250px">
                <el-form-item label="OPENCLAW_HOME">
                  <el-input v-model="config.env.OPENCLAW_HOME" />
                </el-form-item>
                <el-form-item label="OPENCLAW_GATEWAY_PORT">
                  <el-input v-model="config.env.OPENCLAW_GATEWAY_PORT" />
                </el-form-item>
                <el-form-item label="OPENCLAW_DISABLE_BONJOUR">
                  <el-switch v-model="config.env.OPENCLAW_DISABLE_BONJOUR" :active-value="1" :inactive-value="0" />
                </el-form-item>
                <el-form-item label="OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS">
                  <el-input v-model="config.env.OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS" placeholder="* 或具体IP" />
                </el-form-item>
                <el-divider>API Keys</el-divider>
                <el-form-item label="OPENAI_API_KEY">
                  <el-input v-model="config.env.OPENAI_API_KEY" />
                </el-form-item>
                <el-form-item label="ANTHROPIC_API_KEY">
                  <el-input v-model="config.env.ANTHROPIC_API_KEY" />
                </el-form-item>
                <el-form-item label="DEEPSEEK_API_KEY">
                  <el-input v-model="config.env.DEEPSEEK_API_KEY" />
                </el-form-item>
                <el-form-item label="MINIMAX_API_KEY">
                  <el-input v-model="config.env.MINIMAX_API_KEY" />
                </el-form-item>
                <el-form-item label="GEMINI_API_KEY">
                  <el-input v-model="config.env.GEMINI_API_KEY" />
                </el-form-item>
                <el-form-item label="OLLAMA_API_KEY">
                  <el-input v-model="config.env.OLLAMA_API_KEY" placeholder="" />
                </el-form-item>
                <el-form-item label="OPENROUTER_API_KEY">
                  <el-input v-model="config.env.OPENROUTER_API_KEY" />
                </el-form-item>
                <el-form-item label="HUGGINGFACE_HUB_TOKEN">
                  <el-input v-model="config.env.HUGGINGFACE_HUB_TOKEN" />
                </el-form-item>
                <el-form-item label="GROQ_API_KEY">
                  <el-input v-model="config.env.GROQ_API_KEY" />
                </el-form-item>
                <el-form-item label="XAI_API_KEY">
                  <el-input v-model="config.env.XAI_API_KEY" />
                </el-form-item>
                <el-form-item label="COHERE_API_KEY">
                  <el-input v-model="config.env.COHERE_API_KEY" />
                </el-form-item>
                <el-form-item label="MISTRAL_API_KEY">
                  <el-input v-model="config.env.MISTRAL_API_KEY" />
                </el-form-item>
                <el-form-item label="VOYAGE_API_KEY">
                  <el-input v-model="config.env.VOYAGE_API_KEY" />
                </el-form-item>
                <el-form-item label="ZAI_API_KEY">
                  <el-input v-model="config.env.ZAI_API_KEY" />
                </el-form-item>
                <el-form-item label="CEREBRAS_API_KEY">
                  <el-input v-model="config.env.CEREBRAS_API_KEY" />
                </el-form-item>
                <el-form-item label="TOGETHER_API_KEY">
                  <el-input v-model="config.env.TOGETHER_API_KEY" />
                </el-form-item>
                <el-form-item label="MOONSHOT_API_KEY">
                  <el-input v-model="config.env.MOONSHOT_API_KEY" />
                </el-form-item>
                <el-form-item label="KIMI_API_KEY">
                  <el-input v-model="config.env.KIMI_API_KEY" />
                </el-form-item>
                <el-form-item label="VENICE_API_KEY">
                  <el-input v-model="config.env.VENICE_API_KEY" />
                </el-form-item>
                <el-form-item label="NVIDIA_API_KEY">
                  <el-input v-model="config.env.NVIDIA_API_KEY" />
                </el-form-item>
                <el-form-item label="SYNTHETIC_API_KEY">
                  <el-input v-model="config.env.SYNTHETIC_API_KEY" />
                </el-form-item>
                <el-form-item label="KILOCODE_API_KEY">
                  <el-input v-model="config.env.KILOCODE_API_KEY" />
                </el-form-item>
                <el-form-item label="AI_GATEWAY_API_KEY">
                  <el-input v-model="config.env.AI_GATEWAY_API_KEY" />
                </el-form-item>
                <el-form-item label="AZURE_OPENAI_ENDPOINT">
                  <el-input v-model="config.env.AZURE_OPENAI_ENDPOINT" placeholder="https://xxx.openai.azure.com" />
                </el-form-item>
                <el-form-item label="AZURE_OPENAI_DEPLOYMENT">
                  <el-input v-model="config.env.AZURE_OPENAI_DEPLOYMENT" placeholder="gpt-4o" />
                </el-form-item>
                <el-divider>渠道配置</el-divider>
                <el-form-item label="TELEGRAM_BOT_TOKEN">
                  <el-input v-model="config.env.TELEGRAM_BOT_TOKEN" />
                </el-form-item>
                <el-form-item label="DISCORD_BOT_TOKEN">
                  <el-input v-model="config.env.DISCORD_BOT_TOKEN" />
                </el-form-item>
                <el-form-item label="DISCORD_GUILD_ID">
                  <el-input v-model="config.env.DISCORD_GUILD_ID" />
                </el-form-item>
                <el-form-item label="DISCORD_USER_ID">
                  <el-input v-model="config.env.DISCORD_USER_ID" />
                </el-form-item>
                <el-form-item label="FEISHU_APP_ID">
                  <el-input v-model="config.env.FEISHU_APP_ID" />
                </el-form-item>
                <el-form-item label="FEISHU_APP_SECRET">
                  <el-input v-model="config.env.FEISHU_APP_SECRET" />
                </el-form-item>
                <el-divider>其他渠道</el-divider>
                <el-form-item label="WHATSAPP_SESSION_PATH">
                  <el-input v-model="config.env.WHATSAPP_SESSION_PATH" placeholder="/root/.openclaw/credentials/whatsapp" />
                </el-form-item>
                <el-form-item label="SLACK_BOT_TOKEN">
                  <el-input v-model="config.env.SLACK_BOT_TOKEN" placeholder="xoxb-xxx" />
                </el-form-item>
                <el-form-item label="SLACK_TEAM_ID">
                  <el-input v-model="config.env.SLACK_TEAM_ID" placeholder="Txxx" />
                </el-form-item>
                <el-form-item label="SIGNAL电话号码">
                  <el-input v-model="config.env['SIGNAL电话号码']" placeholder="+1234567890" />
                </el-form-item>
              </el-form>
            </el-tab-pane>

            <el-tab-pane label="openclaw.json" name="openclaw">
              <div class="editor-header-actions" style="margin-bottom: 15px; display: flex; align-items: center; gap: 20px;">
                <el-radio-group v-model="configEditMode" size="small">
                  <el-radio-button label="gui">图形化编辑</el-radio-button>
                  <el-radio-button label="raw">源码编辑</el-radio-button>
                </el-radio-group>
                <el-alert v-if="configEditMode === 'gui'" title="提示：图形化编辑模式已覆盖所有官方核心字段，包含布尔值、数值等类型校验。" type="info" :closable="false" show-icon style="flex: 1;" />
              </div>

              <div v-if="configEditMode === 'gui'" class="gui-editor-content">
                <el-collapse v-model="activeGuiPanels">
                  <!-- 基础环境配置 -->
                  <el-collapse-item title="基础环境 (env)" name="env">
                    <el-form label-width="180px">
                      <el-form-item label="Shell 环境 (enabled)">
                        <el-switch :model-value="config.openclaw.env.shellEnv.enabled" disabled />
                        <span class="form-help" style="margin-left: 10px; color: #909399; font-size: 12px;"> (Docker 环境下强制禁用)</span>
                      </el-form-item>
                      <el-form-item label="Shell 超时 (ms)">
                        <el-input-number v-model="config.openclaw.env.shellEnv.timeoutMs" :min="1000" :step="1000" />
                      </el-form-item>
                    </el-form>
                  </el-collapse-item>

                  <!-- 代理默认配置 -->
                  <el-collapse-item title="代理默认值 (agents.defaults)" name="agents_defaults">
                    <el-form label-width="180px">
                      <el-form-item label="默认模型 (primary)">
                        <el-input v-model="config.openclaw.agents.defaults.model.primary" placeholder="anthropic/claude-3-5-sonnet" />
                      </el-form-item>
                      <el-form-item label="PDF 解析模型 (primary)">
                        <el-input v-model="config.openclaw.agents.defaults.pdfModel.primary" />
                      </el-form-item>
                      <el-form-item label="总结历史消息 (enabled)">
                        <el-switch v-model="config.openclaw.agents.defaults.summarizeHistory.enabled" />
                      </el-form-item>
                      <el-form-item label="上下文 Tokens">
                        <el-input-number v-model="config.openclaw.agents.defaults.contextTokens" :min="1" :max="2000000" />
                      </el-form-item>
                      <el-form-item label="并发上限">
                        <el-input-number v-model="config.openclaw.agents.defaults.maxConcurrent" :min="1" :max="32" />
                      </el-form-item>
                    </el-form>
                  </el-collapse-item>

                  <!-- 工具与执行 -->
                  <el-collapse-item title="工具与执行 (tools)" name="tools">
                    <el-form label-width="180px">
                      <el-form-item label="工具配置文件 (profile)">
                        <el-select v-model="config.openclaw.tools.profile">
                          <el-option label="full" value="full" />
                          <el-option label="coding" value="coding" />
                          <el-option label="minimal" value="minimal" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="智能体间通信">
                        <el-switch v-model="config.openclaw.tools.agentToAgent.enabled" />
                      </el-form-item>
                      <el-divider>Exec 执行配置</el-divider>
                      <el-form-item label="超时时间 (秒)">
                        <el-input-number v-model="config.openclaw.tools.exec.timeoutSec" :min="10" />
                      </el-form-item>
                      <el-form-item label="退出时通知">
                        <el-switch v-model="config.openclaw.tools.exec.notifyOnExit" />
                      </el-form-item>
                      <el-form-item label="空执行成功通知">
                        <el-switch v-model="config.openclaw.tools.exec.notifyOnExitEmptySuccess" />
                      </el-form-item>
                    </el-form>
                  </el-collapse-item>

                  <!-- 会话配置 -->
                  <el-collapse-item title="会话管理 (session)" name="session">
                    <el-form label-width="180px">
                      <el-form-item label="保留最近消息数">
                        <el-input-number v-model="config.openclaw.session.keepLastMessages" :min="1" />
                      </el-form-item>
                      <el-form-item label="标题生成模型">
                        <el-input v-model="config.openclaw.session.titleGenerationModel" />
                      </el-form-item>
                    </el-form>
                  </el-collapse-item>

                  <!-- 网关与 Web -->
                  <el-collapse-item title="网关与 Web (gateway & web)" name="gateway_web">
                    <el-form label-width="180px">
                      <el-form-item label="网关绑定 (bind)">
                        <el-select v-model="config.openclaw.gateway.bind">
                          <el-option label="auto" value="auto" />
                          <el-option label="loopback" value="loopback" />
                          <el-option label="lan" value="lan" />
                        </el-select>
                      </el-form-item>
                      <el-divider>Web 搜索/抓取</el-divider>
                      <el-form-item label="Web 搜索启用">
                        <el-switch v-model="config.openclaw.tools.web.search.enabled" />
                      </el-form-item>
                      <el-form-item label="Web 抓取启用">
                        <el-switch v-model="config.openclaw.tools.web.fetch.enabled" />
                      </el-form-item>
                    </el-form>
                  </el-collapse-item>
                </el-collapse>
                <div class="form-tip" style="margin-top: 20px; color: #909399; font-size: 13px;">
                  * 此处 GUI 仅展示 openclaw.json 的部分通用字段。对于 Provider/Media 等核心逻辑，请前往“模型与能力”标签页进行更直观的结构化配置。
                </div>
              </div>

              <div v-show="configEditMode === 'raw'">
                <div class="editor-container" ref="editorContainer"></div>
                <div style="margin-top: 10px;">
                  <el-button size="small" @click="formatJson">格式化 JSON</el-button>
                  <el-button size="small" @click="validateJson">验证 JSON</el-button>
                  <el-button size="small" type="warning" @click="restoreDefaultConfig">恢复默认</el-button>
                </div>
                <div class="editor-tip" style="margin-top: 10px; color: #E6A23C; font-size: 12px;">
                  * 源码编辑模式。建议仅在需要配置此处 GUI 未涵盖的冷门字段时使用。
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="配置对比" name="compare">
              <div class="compare-container">
                <el-alert type="info" :closable="false" style="margin-bottom: 15px;">
                  以下显示当前配置与默认模板的差异对比
                </el-alert>
                <el-row :gutter="20">
                  <el-col :span="12">
                    <el-card>
                      <template #header>
                        <span>当前配置</span>
                      </template>
                      <div class="config-compare">
                        <pre>{{ formatJsonDisplay(currentConfigCompare) }}</pre>
                      </div>
                    </el-card>
                  </el-col>
                  <el-col :span="12">
                    <el-card>
                      <template #header>
                        <span>默认模板</span>
                      </template>
                      <div class="config-compare">
                        <pre>{{ formatJsonDisplay(defaultTemplate) }}</pre>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
                <el-divider>差异分析</el-divider>
                <div v-if="configDiffs.length === 0" class="diff-result success">
                  <el-icon><Check /></el-icon>
                  当前配置与默认模板一致
                </div>
                <div v-else class="diff-list">
                  <el-tag v-for="diff in configDiffs" :key="diff.key" :type="diff.type" style="margin: 5px;">
                    {{ diff.key }}: {{ diff.change }}
                  </el-tag>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane label="模型与能力" name="security">
              <el-tabs v-model="activeSecuritySection" tab-position="top" class="inner-tabs">
                <el-tab-pane label="模型路由" name="routing">
                  <el-form label-width="200px">
                <el-divider>默认模型路由</el-divider>
                <el-form-item label="主对话模型">
                  <el-select v-model="config.openclaw.agents.defaults.model.primary" filterable allow-create default-first-option placeholder="选择或输入模型ID">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="主对话回退模型">
                  <el-select v-model="modelFallbacksInput" multiple filterable allow-create default-first-option placeholder="选择或输入模型列表" style="width: 100%" @change="updateModelFallbacks">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="视觉模型">
                  <el-select v-model="config.openclaw.agents.defaults.imageModel.primary" filterable allow-create default-first-option placeholder="选择或输入模型ID">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="视觉回退模型">
                  <el-select v-model="imageFallbacksInput" multiple filterable allow-create default-first-option placeholder="选择或输入模型列表" style="width: 100%" @change="updateImageFallbacks">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="图像生成模型">
                  <el-select v-model="config.openclaw.agents.defaults.imageGenerationModel.primary" filterable allow-create default-first-option placeholder="选择或输入模型ID">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="图像生成回退模型">
                  <el-select v-model="imageGenerationFallbacksInput" multiple filterable allow-create default-first-option placeholder="选择或输入模型列表" style="width: 100%" @change="updateImageGenerationFallbacks">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="PDF 模型">
                  <el-select v-model="config.openclaw.agents.defaults.pdfModel.primary" filterable allow-create default-first-option placeholder="选择或输入模型ID">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="PDF 回退模型">
                  <el-select v-model="pdfFallbacksInput" multiple filterable allow-create default-first-option placeholder="选择或输入模型列表" style="width: 100%" @change="updatePdfFallbacks">
                    <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Workspace 目录">
                  <el-input v-model="config.openclaw.agents.defaults.workspace" />
                </el-form-item>
                <el-form-item label="上下文 Tokens">
                  <el-input-number v-model="config.openclaw.agents.defaults.contextTokens" :min="1" :max="2000000" />
                </el-form-item>
                <el-form-item label="并发上限">
                  <el-input-number v-model="config.openclaw.agents.defaults.maxConcurrent" :min="1" :max="32" />
                </el-form-item>

                <el-divider>模型别名路由</el-divider>
                <div class="provider-toolbar">
                  <el-button type="primary" plain @click="addAliasModelEntry">新增别名模型</el-button>
                </div>
                <div v-if="aliasModelEntries.length === 0" class="empty-note">当前未配置 `agents.defaults.models` 别名路由。</div>
                <el-card v-for="(entry, index) in aliasModelEntries" :key="`alias-${index}`" class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>{{ entry.key || `alias.${index + 1}` }}</span>
                      <el-button type="danger" link @click="removeAliasModelEntry(index)">删除</el-button>
                    </div>
                  </template>
                  <el-form label-width="150px">
                    <el-form-item label="别名键名">
                      <el-input v-model="entry.key" placeholder="reasoning / planner / coding" />
                    </el-form-item>
                    <el-form-item label="primary">
                      <el-select v-model="entry.primary" filterable allow-create default-first-option placeholder="选择或输入模型ID">
                        <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="fallbacks">
                      <el-select v-model="entry.fallbacksInput" multiple filterable allow-create default-first-option placeholder="选择或输入模型列表" style="width: 100%" @change="(val) => updateAliasFallbacks(val, index)">
                        <el-option v-for="opt in modelOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="附加字段 JSON">
                      <el-input v-model="entry.extraJson" type="textarea" :rows="4" placeholder='{"thinking":"high"}' />
                    </el-form-item>
                  </el-form>
                </el-card>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="Providers" name="providers">
                  <el-form label-width="200px">

                <el-divider>模型目录与 Provider</el-divider>
                <el-form-item label="models.mode">
                  <el-select v-model="config.openclaw.models.mode">
                    <el-option label="merge" value="merge" />
                    <el-option label="replace" value="replace" />
                  </el-select>
                </el-form-item>
                <div class="provider-toolbar">
                  <el-button type="primary" plain @click="addProviderDraft">新增 Provider</el-button>
                </div>
                <div v-if="providerDrafts.length === 0" class="empty-note">当前未配置任何 provider。</div>
                <el-card v-for="(provider, index) in providerDrafts" :key="`provider-${index}`" class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>{{ provider.id || `Provider ${index + 1}` }}</span>
                      <el-button type="danger" link @click="removeProviderDraft(index)">删除</el-button>
                    </div>
                  </template>
                  <el-form label-width="150px">
                    <el-form-item label="Provider ID">
                      <el-input v-model="provider.id" placeholder="openai / anthropic / openrouter" />
                    </el-form-item>
                    <el-form-item label="api">
                      <el-input v-model="provider.api" placeholder="responses / chat.completions" />
                    </el-form-item>
                    <el-form-item label="baseUrl">
                      <el-input v-model="provider.baseUrl" placeholder="https://api.openai.com/v1" />
                    </el-form-item>
                    <el-form-item label="apiKey">
                      <el-input v-model="provider.apiKey" placeholder="可填 env 引用或固定值" />
                    </el-form-item>
                    <el-form-item label="models JSON">
                      <el-input v-model="provider.modelsJson" type="textarea" :rows="4" placeholder='["gpt-5", "gpt-5-mini"]' />
                    </el-form-item>
                    <el-form-item label="headers JSON">
                      <el-input v-model="provider.headersJson" type="textarea" :rows="4" placeholder='{"HTTP-Referer":"https://example.com"}' />
                    </el-form-item>
                    <el-form-item label="附加字段 JSON">
                      <el-input v-model="provider.extraJson" type="textarea" :rows="4" placeholder='{"auth":{"type":"bearer"}}' />
                    </el-form-item>
                  </el-form>
                </el-card>
                <div class="form-tip">复杂 provider 结构会在保存时写回 `models.providers`；更细粒度字段仍可在 `openclaw.json` 标签页精确编辑。</div>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="工具能力" name="tools">
                  <el-form label-width="200px">

                <el-divider>工具能力</el-divider>
                <el-form-item label="tools.profile">
                  <el-select v-model="config.openclaw.tools.profile">
                    <el-option label="minimal" value="minimal" />
                    <el-option label="coding" value="coding" />
                    <el-option label="full" value="full" />
                  </el-select>
                </el-form-item>
                <el-form-item label="额外允许的工具 / group">
                  <el-input v-model="toolAllowInput" placeholder="group:fs, sessions_list, web_search" />
                </el-form-item>
                <el-form-item label="显式禁用的工具 / group">
                  <el-input v-model="toolDenyInput" placeholder="browser, canvas, group:ui" />
                </el-form-item>
                <el-form-item label="启用 Agent to Agent">
                  <el-switch v-model="config.openclaw.tools.agentToAgent.enabled" />
                </el-form-item>

                <el-divider>Media 能力</el-divider>
                <div class="provider-toolbar">
                  <el-button type="primary" plain @click="addMediaEntry">新增 Media 配置项</el-button>
                </div>
                <div v-if="mediaEntries.length === 0" class="empty-note">当前未配置 `tools.media` 细项。</div>
                <el-card v-for="(entry, index) in mediaEntries" :key="`media-${index}`" class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>{{ entry.key || `media.${index + 1}` }}</span>
                      <el-button type="danger" link @click="removeMediaEntry(index)">删除</el-button>
                    </div>
                  </template>
                  <el-form label-width="140px">
                    <el-form-item label="键名">
                      <el-input v-model="entry.key" placeholder="image / audio / video / maxBytesMb" />
                    </el-form-item>
                    <el-form-item label="值类型">
                      <el-select v-model="entry.type">
                        <el-option label="boolean" value="boolean" />
                        <el-option label="number" value="number" />
                        <el-option label="string" value="string" />
                        <el-option label="json" value="json" />
                      </el-select>
                    </el-form-item>
                    <el-form-item label="值" v-if="entry.type === 'boolean'">
                      <el-switch v-model="entry.value" />
                    </el-form-item>
                    <el-form-item label="值" v-else-if="entry.type === 'number'">
                      <el-input-number v-model="entry.value" :min="0" :max="100000000" />
                    </el-form-item>
                    <el-form-item label="值" v-else-if="entry.type === 'string'">
                      <el-input v-model="entry.value" placeholder="字符串值" />
                    </el-form-item>
                    <el-form-item label="值 JSON" v-else>
                      <el-input v-model="entry.value" type="textarea" :rows="4" placeholder='{"enabled":true}' />
                    </el-form-item>
                  </el-form>
                </el-card>

                <el-divider>按 Provider 分配工具</el-divider>
                <div class="provider-toolbar">
                  <el-button type="primary" plain @click="addByProviderEntry">新增 Provider 工具策略</el-button>
                </div>
                <div v-if="byProviderEntries.length === 0" class="empty-note">当前未配置 `tools.byProvider`。</div>
                <el-card v-for="(entry, index) in byProviderEntries" :key="`by-provider-${index}`" class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>{{ entry.provider || `provider-policy.${index + 1}` }}</span>
                      <el-button type="danger" link @click="removeByProviderEntry(index)">删除</el-button>
                    </div>
                  </template>
                  <el-form label-width="150px">
                    <el-form-item label="Provider ID">
                      <el-input v-model="entry.provider" placeholder="openai / anthropic / openrouter" />
                    </el-form-item>
                    <el-form-item label="allow">
                      <el-input v-model="entry.allowInput" placeholder="read_file, web_search, group:fs" />
                    </el-form-item>
                    <el-form-item label="deny">
                      <el-input v-model="entry.denyInput" placeholder="browser, group:ui" />
                    </el-form-item>
                    <el-form-item label="附加字段 JSON">
                      <el-input v-model="entry.extraJson" type="textarea" :rows="4" placeholder='{"profile":"coding"}' />
                    </el-form-item>
                  </el-form>
                </el-card>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="执行与 Web" name="runtime">
                  <el-form label-width="200px">

                <el-divider>Docker 直接执行策略</el-divider>
                <el-alert type="warning" :closable="false" style="margin-bottom: 15px;">
                  当前系统中的所有实例都运行在 Docker 内，因此此处固定为：禁用 sandbox、命令直接在 gateway/容器环境执行。
                </el-alert>
                <el-form-item label="Sandbox 状态">
                  <el-tag type="info">已禁用</el-tag>
                </el-form-item>
                <el-form-item label="Shell Env">
                  <el-switch :model-value="config.openclaw.env.shellEnv.enabled" disabled />
                </el-form-item>
                <el-form-item label="Exec 主机位置">
                  <el-input :model-value="config.openclaw.tools.exec.host" disabled />
                </el-form-item>
                <el-form-item label="Exec 安全模式">
                  <el-input :model-value="config.openclaw.tools.exec.security" disabled />
                </el-form-item>
                <el-form-item label="Exec 审批策略">
                  <el-input :model-value="config.openclaw.tools.exec.ask" disabled />
                </el-form-item>
                <el-form-item label="后台切换毫秒数">
                  <el-input-number v-model="config.openclaw.tools.exec.backgroundMs" :min="0" :max="600000" />
                </el-form-item>
                <el-form-item label="超时秒数">
                  <el-input-number v-model="config.openclaw.tools.exec.timeoutSec" :min="1" :max="7200" />
                </el-form-item>
                <el-form-item label="退出通知">
                  <el-switch v-model="config.openclaw.tools.exec.notifyOnExit" />
                </el-form-item>

                <el-divider>Web 能力</el-divider>
                <el-form-item label="启用网页搜索">
                  <el-switch v-model="config.openclaw.tools.web.search.enabled" />
                </el-form-item>
                <el-form-item label="搜索结果数上限">
                  <el-input-number v-model="config.openclaw.tools.web.search.maxResults" :min="1" :max="50" />
                </el-form-item>
                <el-form-item label="启用网页抓取">
                  <el-switch v-model="config.openclaw.tools.web.fetch.enabled" />
                </el-form-item>
                <el-form-item label="抓取最大字符数">
                  <el-input-number v-model="config.openclaw.tools.web.fetch.maxChars" :min="1000" :max="500000" />
                </el-form-item>
                  </el-form>
                </el-tab-pane>

                <el-tab-pane label="Gateway 与 Channels" name="gateway">
                  <el-form label-width="200px">

                <el-divider>Gateway</el-divider>
                <el-form-item label="绑定模式">
                  <el-select v-model="config.openclaw.gateway.bind">
                    <el-option label="auto" value="auto" />
                    <el-option label="loopback" value="loopback" />
                    <el-option label="lan" value="lan" />
                    <el-option label="tailnet" value="tailnet" />
                    <el-option label="custom" value="custom" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Gateway 端口">
                  <el-input-number v-model="config.openclaw.gateway.port" :min="1" :max="65535" />
                </el-form-item>
                <el-form-item label="认证模式">
                  <el-select v-model="config.openclaw.gateway.auth.mode">
                    <el-option label="password" value="password" />
                    <el-option label="token" value="token" />
                    <el-option label="trusted-proxy" value="trusted-proxy" />
                    <el-option label="none" value="none" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Control UI 启用">
                  <el-switch v-model="config.openclaw.gateway.controlUi.enabled" />
                </el-form-item>
                <el-form-item label="Control UI BasePath">
                  <el-input v-model="config.openclaw.gateway.controlUi.basePath" placeholder="/openclaw" />
                </el-form-item>
                <el-form-item label="Gateway tools.allow">
                  <el-input v-model="gatewayAllowInput" placeholder="gateway, health, metrics" />
                </el-form-item>
                <el-form-item label="Gateway tools.deny">
                  <el-input v-model="gatewayDenyInput" placeholder="browser, terminal" />
                </el-form-item>

                <el-divider>Channels 高级配置</el-divider>
                <el-card class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>Telegram</span>
                    </div>
                  </template>
                  <el-form label-width="150px">
                    <el-form-item label="enabled">
                      <el-switch v-model="config.openclaw.channels.telegram.enabled" />
                    </el-form-item>
                    <el-form-item label="dmPolicy">
                      <el-input v-model="config.openclaw.channels.telegram.dmPolicy" placeholder="pairing" />
                    </el-form-item>
                    <el-form-item label="botToken">
                      <el-input v-model="config.openclaw.channels.telegram.botToken" placeholder="123456:ABC-DEF" />
                    </el-form-item>
                    <el-form-item label="groupPolicy">
                      <el-input v-model="config.openclaw.channels.telegram.groupPolicy" placeholder="open" />
                    </el-form-item>
                    <el-form-item label="streaming">
                      <el-input v-model="config.openclaw.channels.telegram.streaming" placeholder="partial" />
                    </el-form-item>
                  </el-form>
                </el-card>
                <el-card class="sub-card">
                  <template #header>
                    <div class="sub-card-header">
                      <span>Feishu</span>
                    </div>
                  </template>
                  <el-form label-width="150px">
                    <el-form-item label="enabled">
                      <el-switch v-model="config.openclaw.channels.feishu.enabled" />
                    </el-form-item>
                    <el-form-item label="appId">
                      <el-input v-model="config.openclaw.channels.feishu.appId" placeholder="cli_xxx" />
                    </el-form-item>
                    <el-form-item label="appSecret">
                      <el-input v-model="config.openclaw.channels.feishu.appSecret" placeholder="xxx" />
                    </el-form-item>
                    <el-form-item label="connectionMode">
                      <el-input v-model="config.openclaw.channels.feishu.connectionMode" placeholder="websocket" />
                    </el-form-item>
                    <el-form-item label="domain">
                      <el-input v-model="config.openclaw.channels.feishu.domain" placeholder="feishu" />
                    </el-form-item>
                    <el-form-item label="groupPolicy">
                      <el-input v-model="config.openclaw.channels.feishu.groupPolicy" placeholder="open" />
                    </el-form-item>
                  </el-form>
                </el-card>
                  </el-form>
                </el-tab-pane>
              </el-tabs>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check } from '@element-plus/icons-vue'
import { groupApi, instanceApi, configApi } from '../api'
import { Codemirror } from 'vue-codemirror'
import { json } from '@codemirror/lang-json'
import { EditorView } from '@codemirror/view'

const editorExtensions = [
  json(),
  EditorView.lineWrapping,
  EditorView.theme({
    "&": {
      fontSize: "14px"
    },
    ".cm-content": {
      fontFamily: "Fira Code, monospace"
    },
    // Zebra striping
    ".cm-line:nth-child(even)": {
      backgroundColor: "#f9f9f9"
    },
    // Highlight active line
    ".cm-activeLine": {
      backgroundColor: "#e8f0fe"
    }
  })
]

const route = useRoute()

const configType = ref('instance')
const selectedTarget = ref('')
const activeTab = ref('env')
const activeSecuritySection = ref('routing')
const configEditMode = ref('gui') // 'gui' or 'raw'
const activeGuiPanels = ref(['env', 'agents_defaults', 'tools'])
const activeTemplates = ref(['openai'])
const activeChannelTemplates = ref(['telegram'])

const groups = ref([])
const instances = ref([])
const defaultConfigBundle = ref({ env: {}, openclaw: { model_knowledge: { providers: [] } } })
const modelOptions = computed(() => {
  const providers = defaultConfigBundle.value?.openclaw?.model_knowledge?.providers || []
  const options = []
  providers.forEach(p => {
    p.models.forEach(m => {
      options.push({
        value: `${p.id}/${m}`,
        label: `${p.name}: ${m}`
      })
    })
  })
  return options
})
const toolAllowInput = ref('')
const toolDenyInput = ref('')
const modelFallbacksInput = ref([])
const imageFallbacksInput = ref([])
const imageGenerationFallbacksInput = ref([])
const pdfFallbacksInput = ref([])
const aliasModelEntries = ref([])
const providerDrafts = ref([])
const mediaEntries = ref([])
const byProviderEntries = ref([])
const gatewayAllowInput = ref('')
const gatewayDenyInput = ref('')

const templates = ref({
  openai: { OPENAI_API_KEY: '' },
  anthropic: { ANTHROPIC_API_KEY: '' },
  google: { GEMINI_API_KEY: '' },
  azure: { AZURE_OPENAI_API_KEY: '', AZURE_OPENAI_ENDPOINT: '', AZURE_OPENAI_DEPLOYMENT: '' },
  deepseek: { DEEPSEEK_API_KEY: '' },
  minimax: { MINIMAX_API_KEY: '' },
  ollama: { OLLAMA_API_KEY: '' },
  openrouter: { OPENROUTER_API_KEY: '' },
  huggingface: { HUGGINGFACE_HUB_TOKEN: '' },
  groq: { GROQ_API_KEY: '' },
  xai: { XAI_API_KEY: '' },
  cohere: { COHERE_API_KEY: '' },
  mistral: { MISTRAL_API_KEY: '' },
  voyage: { VOYAGE_API_KEY: '' },
  zai: { ZAI_API_KEY: '' },
  cerebras: { CEREBRAS_API_KEY: '' },
  together: { TOGETHER_API_KEY: '' },
  moonshot: { MOONSHOT_API_KEY: '' },
  kimi: { KIMI_API_KEY: '' },
  venice: { VENICE_API_KEY: '' },
  nvidia: { NVIDIA_API_KEY: '' },
  synthetic: { SYNTHETIC_API_KEY: '' },
  kilocode: { KILOCODE_API_KEY: '' },
  ai_gateway: { AI_GATEWAY_API_KEY: '' }
})

const channelTemplates = ref({
  telegram: { TELEGRAM_BOT_TOKEN: '' },
  discord: { DISCORD_BOT_TOKEN: '', DISCORD_GUILD_ID: '', DISCORD_USER_ID: '' },
  feishu: { FEISHU_APP_ID: '', FEISHU_APP_SECRET: '' },
  whatsapp: { WHATSAPP_SESSION_PATH: '' },
  slack: { SLACK_BOT_TOKEN: '', SLACK_APP_TOKEN: '', SLACK_TEAM_ID: '' },
  signal: { SIGNAL_PHONE_NUMBER: '', 'SIGNAL电话号码': '' }
})

const config = ref({
  env: {},
  openclaw: {
    env: {
      vars: {},
      shellEnv: {
        enabled: false,
        timeoutMs: 15000
      }
    },
    models: {
      mode: 'merge',
      providers: {}
    },
    agents: {
      defaults: {
        model: { primary: '', fallbacks: [] },
        imageModel: { primary: '', fallbacks: [] },
        imageGenerationModel: { primary: '', fallbacks: [] },
        pdfModel: { primary: '', fallbacks: [] },
        models: {},
        summarizeHistory: { enabled: true }
      }
    },
    tools: {
      profile: 'full',
      allow: [],
      deny: [],
      byProvider: {},
      media: {},
      web: {
        search: { enabled: true, maxResults: 5, timeoutSeconds: 30, cacheTtlMinutes: 15 },
        fetch: { enabled: true, maxChars: 50000, maxCharsCap: 50000, timeoutSeconds: 30, cacheTtlMinutes: 15 }
      },
      agentToAgent: { enabled: true },
      exec: {
        backgroundMs: 10000,
        timeoutSec: 1800,
        cleanupMs: 1800000,
        notifyOnExit: true,
        notifyOnExitEmptySuccess: false,
        host: 'gateway',
        security: 'full',
        ask: 'off'
      },
      elevated: { enabled: true, allowFrom: {} }
    },
    session: {
      keepLastMessages: 20,
      titleGenerationModel: ''
    },
    gateway: {
      port: 18789,
      bind: 'lan',
      mode: 'local',
      controlUi: { enabled: true, basePath: '/openclaw', allowedOrigins: [] },
      tools: { allow: [], deny: [] },
      auth: {
        mode: 'password',
        allowTailscale: true,
        rateLimit: { maxAttempts: 10, windowMs: 60000, lockoutMs: 300000, exemptLoopback: true }
      }
    },
    channels: {
      telegram: { enabled: false, dmPolicy: 'pairing', botToken: '', groupPolicy: 'open', streaming: 'partial' },
      feishu: { enabled: false, appId: '', appSecret: '', connectionMode: 'websocket', domain: 'feishu', groupPolicy: 'open' }
    }
  }
})

const openclawJsonStr = ref('')

const defaultTemplate = ref({})

const currentConfigCompare = ref({})
const configDiffs = ref([])

const cloneDeep = (value) => JSON.parse(JSON.stringify(value ?? {}))

const splitCommaList = (value) => {
  if (!value) return []
  if (Array.isArray(value)) {
    return value.map(item => String(item).trim()).filter(Boolean)
  }
  if (typeof value !== 'string') {
    return []
  }
  return value.split(',').map(item => item.trim()).filter(Boolean)
}

const joinCommaList = (value) => {
  if (Array.isArray(value)) return value.join(', ')
  if (typeof value === 'string') return value
  return ''
}

const parseJsonOrFallback = (value, fallback) => {
  if (!value || !String(value).trim()) return fallback
  try {
    return JSON.parse(value)
  } catch {
    return fallback
  }
}

const parseJsonStrict = (value, fallback) => {
  if (!value || !String(value).trim()) return fallback
  return JSON.parse(value)
}

const stringifyJsonField = (value, fallback = '') => {
  if (value === undefined || value === null) return fallback
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return fallback
  }
}

const normalizeMediaEntry = (key, value) => {
  if (typeof value === 'boolean') {
    return { key, type: 'boolean', value }
  }
  if (typeof value === 'number') {
    return { key, type: 'number', value }
  }
  if (typeof value === 'string') {
    return { key, type: 'string', value }
  }

  return {
    key,
    type: 'json',
    value: stringifyJsonField(value, '{}')
  }
}

const createEmptyProviderDraft = () => ({
  id: '',
  api: '',
  baseUrl: '',
  apiKey: '',
  modelsJson: '[]',
  headersJson: '{}',
  extraJson: '{}'
})

const createEmptyMediaEntry = () => ({
  key: '',
  type: 'boolean',
  value: false
})

const createEmptyAliasModelEntry = () => ({
  key: '',
  primary: '',
  fallbacksInput: [],
  extraJson: '{}'
})

const createEmptyByProviderEntry = () => ({
  provider: '',
  allowInput: '',
  denyInput: '',
  extraJson: '{}'
})

const validateStructuredConfig = () => {
  const errors = []

  const pushJsonError = (label, index, error) => {
    errors.push(`${label} 第 ${index + 1} 项 JSON 无效: ${error.message}`)
  }

  const seenAliasKeys = new Set()
  aliasModelEntries.value.forEach((entry, index) => {
    const key = entry.key?.trim()
    if (!key) {
      errors.push(`模型别名第 ${index + 1} 项缺少键名`)
      return
    }
    if (seenAliasKeys.has(key)) {
      errors.push(`模型别名键名重复: ${key}`)
    }
    seenAliasKeys.add(key)
    if (!entry.primary?.trim()) {
      errors.push(`模型别名 ${key} 缺少 primary`)
    }
    try {
      parseJsonStrict(entry.extraJson, {})
    } catch (error) {
      pushJsonError('模型别名', index, error)
    }
  })

  const seenProviderIds = new Set()
  providerDrafts.value.forEach((entry, index) => {
    const providerId = entry.id?.trim()
    if (!providerId) {
      errors.push(`Provider 第 ${index + 1} 项缺少 ID`)
      return
    }
    if (seenProviderIds.has(providerId)) {
      errors.push(`Provider ID 重复: ${providerId}`)
    }
    seenProviderIds.add(providerId)
    try {
      parseJsonStrict(entry.modelsJson, [])
    } catch (error) {
      pushJsonError('Provider models', index, error)
    }
    try {
      parseJsonStrict(entry.headersJson, {})
    } catch (error) {
      pushJsonError('Provider headers', index, error)
    }
    try {
      parseJsonStrict(entry.extraJson, {})
    } catch (error) {
      pushJsonError('Provider extra', index, error)
    }
  })

  const seenMediaKeys = new Set()
  mediaEntries.value.forEach((entry, index) => {
    const key = entry.key?.trim()
    if (!key) {
      errors.push(`Media 第 ${index + 1} 项缺少键名`)
      return
    }
    if (seenMediaKeys.has(key)) {
      errors.push(`Media 键名重复: ${key}`)
    }
    seenMediaKeys.add(key)
    if (entry.type === 'number' && Number.isNaN(Number(entry.value))) {
      errors.push(`Media ${key} 的 number 值无效`)
    }
    if (entry.type === 'json') {
      try {
        parseJsonStrict(entry.value, {})
      } catch (error) {
        pushJsonError('Media', index, error)
      }
    }
  })

  const seenByProvider = new Set()
  byProviderEntries.value.forEach((entry, index) => {
    const provider = entry.provider?.trim()
    if (!provider) {
      errors.push(`Provider 工具策略第 ${index + 1} 项缺少 Provider ID`)
      return
    }
    if (seenByProvider.has(provider)) {
      errors.push(`Provider 工具策略重复: ${provider}`)
    }
    seenByProvider.add(provider)
    try {
      parseJsonStrict(entry.extraJson, {})
    } catch (error) {
      pushJsonError('Provider 工具策略', index, error)
    }
  })

  return errors
}

const enforceDockerExecutionPolicy = () => {
  config.value.openclaw.env.shellEnv.enabled = false
  config.value.openclaw.tools.exec.host = 'gateway'
  config.value.openclaw.tools.exec.security = 'full'
  config.value.openclaw.tools.exec.ask = 'off'
  delete config.value.openclaw.sandbox
  if (config.value.openclaw.agents?.defaults?.sandbox) {
    delete config.value.openclaw.agents.defaults.sandbox
  }
}

const syncProviderDraftsFromConfig = () => {
  const providers = config.value.openclaw.models.providers || {}
  providerDrafts.value = Object.entries(providers).map(([id, provider]) => {
    const { api = '', baseUrl = '', apiKey = '', models, headers, ...extra } = provider || {}
    return {
      id,
      api,
      baseUrl,
      apiKey,
      modelsJson: stringifyJsonField(models, '[]'),
      headersJson: stringifyJsonField(headers, '{}'),
      extraJson: stringifyJsonField(extra, '{}')
    }
  })
}

const syncAliasModelEntriesFromConfig = () => {
  const models = config.value.openclaw.agents.defaults.models || {}
  aliasModelEntries.value = Object.entries(models).map(([key, val]) => ({
    key,
    primary: val.primary || '',
    fallbacksInput: splitCommaList(val.fallbacks || ''),
    extraJson: stringifyJsonField(val.params || {}, '{}')
  }))
}

const syncMediaEntriesFromConfig = () => {
  const media = config.value.openclaw.tools.media || {}
  mediaEntries.value = Object.entries(media).map(([key, value]) => normalizeMediaEntry(key, value))
}

const syncByProviderEntriesFromConfig = () => {
  const byProvider = config.value.openclaw.tools.byProvider || {}
  byProviderEntries.value = Object.entries(byProvider).map(([provider, value]) => {
    const allow = Array.isArray(value?.allow) ? value.allow : []
    const deny = Array.isArray(value?.deny) ? value.deny : []
    const extra = value && typeof value === 'object'
      ? Object.fromEntries(Object.entries(value).filter(([entryKey]) => !['allow', 'deny'].includes(entryKey)))
      : {}

    return {
      provider,
      allowInput: joinCommaList(allow),
      denyInput: joinCommaList(deny),
      extraJson: stringifyJsonField(extra, '{}')
    }
  })
}

const applyProviderDraftsToConfig = () => {
  const providers = {}
  providerDrafts.value.forEach((draft) => {
    const id = draft.id?.trim()
    if (!id) return

    const provider = {}
    if (draft.api?.trim()) provider.api = draft.api.trim()
    if (draft.baseUrl?.trim()) provider.baseUrl = draft.baseUrl.trim()
    if (draft.apiKey?.trim()) provider.apiKey = draft.apiKey.trim()

    const models = parseJsonOrFallback(draft.modelsJson, [])
    if ((Array.isArray(models) && models.length > 0) || (!Array.isArray(models) && Object.keys(models || {}).length > 0)) {
      provider.models = models
    }

    const headers = parseJsonOrFallback(draft.headersJson, {})
    if (headers && typeof headers === 'object' && Object.keys(headers).length > 0) {
      provider.headers = headers
    }

    const extra = parseJsonOrFallback(draft.extraJson, {})
    if (extra && typeof extra === 'object') {
      Object.assign(provider, extra)
    }

    providers[id] = provider
  })

  config.value.openclaw.models.providers = providers
}

const applyAliasModelEntriesToConfig = () => {
  const models = {}
  aliasModelEntries.value.forEach(entry => {
    if (entry.key) {
      models[entry.key] = {
        primary: entry.primary,
        fallbacks: splitCommaList(entry.fallbacksInput),
        params: parseJsonOrFallback(entry.extraJson, {})
      }
    }
  })
  config.value.openclaw.agents.defaults.models = models
}

const applyMediaEntriesToConfig = () => {
  const media = {}
  mediaEntries.value.forEach((entry) => {
    const key = entry.key?.trim()
    if (!key) return

    if (entry.type === 'boolean') {
      media[key] = !!entry.value
    } else if (entry.type === 'number') {
      media[key] = Number(entry.value || 0)
    } else if (entry.type === 'string') {
      media[key] = entry.value ?? ''
    } else {
      media[key] = parseJsonOrFallback(entry.value, {})
    }
  })

  config.value.openclaw.tools.media = media
}

const applyByProviderEntriesToConfig = () => {
  const byProvider = {}
  byProviderEntries.value.forEach((entry) => {
    const provider = entry.provider?.trim()
    if (!provider) return

    const providerConfig = {}
    const allow = splitCommaList(entry.allowInput)
    const deny = splitCommaList(entry.denyInput)
    if (allow.length > 0) {
      providerConfig.allow = allow
    }
    if (deny.length > 0) {
      providerConfig.deny = deny
    }

    const extra = parseJsonOrFallback(entry.extraJson, {})
    if (extra && typeof extra === 'object') {
      Object.assign(providerConfig, extra)
    }

    byProvider[provider] = providerConfig
  })

  config.value.openclaw.tools.byProvider = byProvider
}

const addProviderDraft = () => {
  providerDrafts.value.push(createEmptyProviderDraft())
}

const removeProviderDraft = (index) => {
  providerDrafts.value.splice(index, 1)
}

const addAliasModelEntry = () => {
  aliasModelEntries.value.push(createEmptyAliasModelEntry())
}

const removeAliasModelEntry = (index) => {
  aliasModelEntries.value.splice(index, 1)
}

const addMediaEntry = () => {
  mediaEntries.value.push(createEmptyMediaEntry())
}

const removeMediaEntry = (index) => {
  mediaEntries.value.splice(index, 1)
}

const addByProviderEntry = () => {
  byProviderEntries.value.push(createEmptyByProviderEntry())
}

const removeByProviderEntry = (index) => {
  byProviderEntries.value.splice(index, 1)
}

const normalizeModelConfig = (value) => {
  if (typeof value === 'string') {
    return { primary: value, fallbacks: [] }
  }

  return {
    primary: value?.primary || '',
    fallbacks: splitCommaList(value?.fallbacks)
  }
}

const deepMergeObjects = (base, update) => {
  const result = cloneDeep(base)
  Object.entries(update || {}).forEach(([key, value]) => {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      result[key] &&
      typeof result[key] === 'object' &&
      !Array.isArray(result[key])
    ) {
      result[key] = deepMergeObjects(result[key], value)
    } else {
      result[key] = value
    }
  })
  return result
}

const ensureConfigShape = () => {
  const env = config.value.env || {}
  config.value.env = env

  const openclaw = config.value.openclaw || {}
  config.value.openclaw = openclaw

  openclaw.env = openclaw.env || {}
  openclaw.env.vars = openclaw.env.vars || {}
  openclaw.env.shellEnv = {
    enabled: !!openclaw.env.shellEnv?.enabled,
    timeoutMs: openclaw.env.shellEnv?.timeoutMs ?? 15000
  }

  openclaw.models = openclaw.models || {}
  openclaw.models.mode = openclaw.models.mode || 'merge'
  openclaw.models.providers = openclaw.models.providers || {}

  openclaw.agents = openclaw.agents || {}
  openclaw.agents.defaults = openclaw.agents.defaults || {}
  const defaults = openclaw.agents.defaults
  defaults.model = normalizeModelConfig(defaults.model)
  defaults.imageModel = normalizeModelConfig(defaults.imageModel)
  defaults.imageGenerationModel = normalizeModelConfig(defaults.imageGenerationModel)
  defaults.pdfModel = normalizeModelConfig(defaults.pdfModel)
  defaults.models = defaults.models || {}
  defaults.summarizeHistory = {
    enabled: defaults.summarizeHistory?.enabled ?? true
  }
  defaults.workspace = defaults.workspace || '/root/.openclaw/workspace'
  defaults.pdfMaxBytesMb = defaults.pdfMaxBytesMb ?? 10
  defaults.pdfMaxPages = defaults.pdfMaxPages ?? 20
  defaults.thinkingDefault = defaults.thinkingDefault || 'low'
  defaults.verboseDefault = defaults.verboseDefault || 'off'
  defaults.elevatedDefault = defaults.elevatedDefault || 'on'
  defaults.timeoutSeconds = defaults.timeoutSeconds ?? 600
  defaults.mediaMaxMb = defaults.mediaMaxMb ?? 5
  defaults.contextTokens = defaults.contextTokens ?? 200000
  defaults.maxConcurrent = defaults.maxConcurrent ?? 3
  if (defaults.sandbox) {
    delete defaults.sandbox
  }

  openclaw.tools = openclaw.tools || {}
  openclaw.tools.profile = openclaw.tools.profile || 'full'
  openclaw.tools.allow = Array.isArray(openclaw.tools.allow) ? openclaw.tools.allow : []
  openclaw.tools.deny = Array.isArray(openclaw.tools.deny) ? openclaw.tools.deny : []
  openclaw.tools.byProvider = openclaw.tools.byProvider || {}
  openclaw.tools.media = openclaw.tools.media || {}
  openclaw.tools.web = openclaw.tools.web || {}
  openclaw.tools.web.search = {
    enabled: openclaw.tools.web.search?.enabled ?? true,
    maxResults: openclaw.tools.web.search?.maxResults ?? 5,
    timeoutSeconds: openclaw.tools.web.search?.timeoutSeconds ?? 30,
    cacheTtlMinutes: openclaw.tools.web.search?.cacheTtlMinutes ?? 15
  }
  openclaw.tools.web.fetch = {
    enabled: openclaw.tools.web.fetch?.enabled ?? true,
    maxChars: openclaw.tools.web.fetch?.maxChars ?? 50000,
    maxCharsCap: openclaw.tools.web.fetch?.maxCharsCap ?? 50000,
    timeoutSeconds: openclaw.tools.web.fetch?.timeoutSeconds ?? 30,
    cacheTtlMinutes: openclaw.tools.web.fetch?.cacheTtlMinutes ?? 15
  }
  openclaw.tools.agentToAgent = {
    enabled: openclaw.tools.agentToAgent?.enabled ?? true
  }
  openclaw.tools.exec = {
    backgroundMs: openclaw.tools.exec?.backgroundMs ?? 10000,
    timeoutSec: openclaw.tools.exec?.timeoutSec ?? 1800,
    cleanupMs: openclaw.tools.exec?.cleanupMs ?? 1800000,
    notifyOnExit: openclaw.tools.exec?.notifyOnExit ?? true,
    notifyOnExitEmptySuccess: openclaw.tools.exec?.notifyOnExitEmptySuccess ?? false,
    host: 'gateway',
    security: 'full',
    ask: 'off'
  }
  openclaw.tools.elevated = {
    enabled: openclaw.tools.elevated?.enabled ?? true,
    allowFrom: openclaw.tools.elevated?.allowFrom || {}
  }

  openclaw.session = openclaw.session || {}
  openclaw.session.keepLastMessages = openclaw.session.keepLastMessages ?? 20
  openclaw.session.titleGenerationModel = openclaw.session.titleGenerationModel || ''

  openclaw.gateway = openclaw.gateway || {}
  openclaw.gateway.port = openclaw.gateway.port ?? Number(env.OPENCLAW_GATEWAY_PORT || 18789)
  openclaw.gateway.bind = openclaw.gateway.bind || 'lan'
  openclaw.gateway.mode = openclaw.gateway.mode || 'local'
  openclaw.gateway.controlUi = openclaw.gateway.controlUi || {}
  openclaw.gateway.controlUi.enabled = openclaw.gateway.controlUi.enabled ?? true
  openclaw.gateway.controlUi.basePath = openclaw.gateway.controlUi.basePath || '/openclaw'
  openclaw.gateway.controlUi.allowedOrigins = Array.isArray(openclaw.gateway.controlUi.allowedOrigins)
    ? openclaw.gateway.controlUi.allowedOrigins
    : []
  openclaw.gateway.tools = openclaw.gateway.tools || {}
  openclaw.gateway.tools.allow = Array.isArray(openclaw.gateway.tools.allow) ? openclaw.gateway.tools.allow : []
  openclaw.gateway.tools.deny = Array.isArray(openclaw.gateway.tools.deny) ? openclaw.gateway.tools.deny : []
  openclaw.gateway.auth = openclaw.gateway.auth || {}
  openclaw.gateway.auth.mode = openclaw.gateway.auth.mode || 'password'
  openclaw.gateway.auth.allowTailscale = openclaw.gateway.auth.allowTailscale ?? true
  openclaw.gateway.auth.rateLimit = openclaw.gateway.auth.rateLimit || {
    maxAttempts: 10,
    windowMs: 60000,
    lockoutMs: 300000,
    exemptLoopback: true
  }

  if (openclaw.sandbox) {
    delete openclaw.sandbox
  }

  openclaw.channels = openclaw.channels || {}
  openclaw.channels.telegram = {
    enabled: openclaw.channels.telegram?.enabled ?? false,
    dmPolicy: openclaw.channels.telegram?.dmPolicy || 'pairing',
    botToken: openclaw.channels.telegram?.botToken || '',
    groupPolicy: openclaw.channels.telegram?.groupPolicy || 'open',
    streaming: openclaw.channels.telegram?.streaming || 'partial'
  }
  openclaw.channels.feishu = {
    enabled: openclaw.channels.feishu?.enabled ?? false,
    appId: openclaw.channels.feishu?.appId || '',
    appSecret: openclaw.channels.feishu?.appSecret || '',
    connectionMode: openclaw.channels.feishu?.connectionMode || 'websocket',
    domain: openclaw.channels.feishu?.domain || 'feishu',
    groupPolicy: openclaw.channels.feishu?.groupPolicy || 'open'
  }

  enforceDockerExecutionPolicy()
}

ensureConfigShape()

const syncStructuredInputsFromConfig = () => {
  const openclaw = config.value.openclaw
  
  // Sync comma lists to array for multi-select
  modelFallbacksInput.value = splitCommaList(openclaw.agents.defaults.model.fallbacks || '')
  imageFallbacksInput.value = splitCommaList(openclaw.agents.defaults.imageModel.fallbacks || '')
  imageGenerationFallbacksInput.value = splitCommaList(openclaw.agents.defaults.imageGenerationModel.fallbacks || '')
  pdfFallbacksInput.value = splitCommaList(openclaw.agents.defaults.pdfModel.fallbacks || '')
  
  toolAllowInput.value = joinCommaList(openclaw.tools.allow)
  toolDenyInput.value = joinCommaList(openclaw.tools.deny)
  
  syncProviderDraftsFromConfig()
  syncMediaEntriesFromConfig()
  syncAliasModelEntriesFromConfig()
  syncByProviderEntriesFromConfig()
}

const updateModelFallbacks = (val) => {
  config.value.openclaw.agents.defaults.model.fallbacks = splitCommaList(val)
}

const updateImageFallbacks = (val) => {
  config.value.openclaw.agents.defaults.imageModel.fallbacks = splitCommaList(val)
}

const updateImageGenerationFallbacks = (val) => {
  config.value.openclaw.agents.defaults.imageGenerationModel.fallbacks = splitCommaList(val)
}

const updatePdfFallbacks = (val) => {
  config.value.openclaw.agents.defaults.pdfModel.fallbacks = splitCommaList(val)
}

const updateAliasFallbacks = (val, index) => {
  if (aliasModelEntries.value[index]) {
    aliasModelEntries.value[index].fallbacksInput = val
  }
}


const applyStructuredInputsToConfig = () => {
  ensureConfigShape()
  config.value.openclaw.tools.allow = splitCommaList(toolAllowInput.value)
  config.value.openclaw.tools.deny = splitCommaList(toolDenyInput.value)
  config.value.openclaw.gateway.tools.allow = splitCommaList(gatewayAllowInput.value)
  config.value.openclaw.gateway.tools.deny = splitCommaList(gatewayDenyInput.value)
  
  config.value.openclaw.agents.defaults.model.fallbacks = splitCommaList(modelFallbacksInput.value)
  config.value.openclaw.agents.defaults.imageModel.fallbacks = splitCommaList(imageFallbacksInput.value)
  config.value.openclaw.agents.defaults.imageGenerationModel.fallbacks = splitCommaList(imageGenerationFallbacksInput.value)
  config.value.openclaw.agents.defaults.pdfModel.fallbacks = splitCommaList(pdfFallbacksInput.value)

  applyAliasModelEntriesToConfig()
  applyProviderDraftsToConfig()
  applyMediaEntriesToConfig()
  applyByProviderEntriesToConfig()
  enforceDockerExecutionPolicy()
}

const loadDefaultBundle = async () => {
  const defaults = await configApi.getDefaults()
  defaultConfigBundle.value = cloneDeep(defaults)
  defaultTemplate.value = cloneDeep(defaults.openclaw || {})
  config.value = cloneDeep(defaults)
  ensureConfigShape()
  syncStructuredInputsFromConfig()
  openclawJsonStr.value = JSON.stringify(config.value.openclaw, null, 2)
}

const syncJsonEditorFromConfig = () => {
  openclawJsonStr.value = JSON.stringify(config.value.openclaw || {}, null, 2)
}

const syncConfigFromJsonEditor = () => {
  const parsed = JSON.parse(openclawJsonStr.value || '{}')
  config.value.openclaw = parsed
  ensureConfigShape()
  syncStructuredInputsFromConfig()
}

const loadGroups = async () => {
  try {
    groups.value = await groupApi.getAll()
  } catch (error) {
    ElMessage.error('获取群组失败')
  }
}

const loadInstances = async () => {
  try {
    instances.value = await instanceApi.getAll()
  } catch (error) {
    ElMessage.error('获取实例失败')
  }
}

const loadConfig = async () => {
  if (!selectedTarget.value) {
    ElMessage.warning('请先选择配置目标')
    return
  }

  try {
    if (!defaultConfigBundle.value.openclaw || Object.keys(defaultConfigBundle.value.openclaw).length === 0) {
      await loadDefaultBundle()
    }

    let configData
    if (configType.value === 'instance') {
      configData = await instanceApi.getConfig(selectedTarget.value)
    } else {
      configData = await groupApi.getConfig(selectedTarget.value)
    }

    config.value = {
      env: deepMergeObjects(defaultConfigBundle.value.env || {}, configData.env || {}),
      openclaw: deepMergeObjects(defaultConfigBundle.value.openclaw || {}, configData.openclaw || {})
    }

    ensureConfigShape()
    syncStructuredInputsFromConfig()
    openclawJsonStr.value = JSON.stringify(config.value.openclaw, null, 2)
    
    currentConfigCompare.value = configData.openclaw || {}
    computeConfigDiffs()
    
    ElMessage.success('配置加载成功')
  } catch (error) {
    ElMessage.error('加载配置失败: ' + error)
  }
}

const saveConfig = async () => {
  if (!selectedTarget.value) {
    ElMessage.warning('请先选择配置目标')
    return
  }

  try {
    if (activeTab.value === 'security') {
      const validationErrors = validateStructuredConfig()
      if (validationErrors.length > 0) {
        ElMessage.error(validationErrors[0])
        return
      }
    }

    applyStructuredInputsToConfig()

    if (activeTab.value === 'openclaw') {
      try {
        syncConfigFromJsonEditor()
      } catch (e) {
        activeTab.value = 'openclaw'
        ElMessage.error('openclaw.json 格式错误，请检查并修正后再保存')
        return
      }
    } else {
      syncJsonEditorFromConfig()
    }

    const data = {
      env_vars: config.value.env,
      openclaw_json: config.value.openclaw,
      replace: true
    }

    if (configType.value === 'instance') {
      await instanceApi.updateConfig(selectedTarget.value, data)
    } else {
      await groupApi.updateConfig(selectedTarget.value, data)
    }

    // Refresh comparison state after save
    currentConfigCompare.value = JSON.parse(JSON.stringify(config.value.openclaw))
    computeConfigDiffs()

    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('保存配置失败: ' + error)
  }
}

const applyTemplates = () => {
  Object.values(templates.value).forEach(provider => {
    Object.entries(provider).forEach(([key, value]) => {
      if (value) {
        config.value.env[key] = value
      }
    })
  })
  ElMessage.success('模板已应用到当前配置')
}

const saveTemplates = async () => {
  try {
    await configApi.saveTemplates(templates.value)
    ElMessage.success('模板保存成功')
  } catch (error) {
    ElMessage.error('保存模板失败: ' + error)
  }
}

const formatJson = () => {
  try {
    syncConfigFromJsonEditor()
    syncJsonEditorFromConfig()
    computeConfigDiffs()
    ElMessage.success('JSON 已格式化')
  } catch (error) {
    ElMessage.error('JSON 格式错误: ' + error.message)
  }
}

const computeConfigDiffs = () => {
  const diffs = []
  const current = currentConfigCompare.value
  const defaultTpl = defaultTemplate.value
  
  const compareObjects = (curr, def, prefix = '') => {
    for (const key in def) {
      const fullKey = prefix ? `${prefix}.${key}` : key
      if (typeof def[key] === 'object' && def[key] !== null && !Array.isArray(def[key])) {
        compareObjects(curr?.[key] || {}, def[key], fullKey)
      } else {
        const currVal = curr?.[key]
        const defVal = def[key]
        if (JSON.stringify(currVal) !== JSON.stringify(defVal)) {
          diffs.push({
            key: fullKey,
            current: currVal !== undefined ? JSON.stringify(currVal) : '(未设置)',
            default: JSON.stringify(defVal),
            change: currVal !== undefined ? `当前: ${JSON.stringify(currVal)}` : '(新增)',
            type: currVal !== undefined ? 'warning' : 'success'
          })
        }
      }
    }
  }
  
  compareObjects(current, defaultTpl)
  configDiffs.value = diffs
}

const formatJsonDisplay = (obj) => {
  if (!obj) return '{}'
  try {
    return JSON.stringify(obj, null, 2)
  } catch {
    return String(obj)
  }
}

const validateJson = () => {
  try {
    syncConfigFromJsonEditor()
    ElMessage.success('JSON 格式正确')
  } catch (error) {
    ElMessage.error('JSON 格式错误: ' + error.message)
  }
}

const restoreDefaultConfig = () => {
  ElMessageBox.confirm(
    '确定要恢复默认配置吗？这将覆盖当前编辑器中的内容。',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    config.value.openclaw = JSON.parse(JSON.stringify(defaultTemplate.value))
    syncStructuredInputsFromConfig()
    openclawJsonStr.value = JSON.stringify(config.value.openclaw, null, 2)
    computeConfigDiffs()
    ElMessage.success('已恢复默认配置')
  }).catch(() => {})
}

const loadTemplates = async () => {
  try {
    const res = await configApi.getTemplates()
    if (res.byok) {
      Object.keys(res.byok).forEach(key => {
        if (templates.value[key]) {
          templates.value[key] = { ...templates.value[key], ...res.byok[key] }
        }
      })
    }
    if (res.channels) {
      Object.keys(res.channels).forEach(key => {
        if (channelTemplates.value[key]) {
          channelTemplates.value[key] = { ...channelTemplates.value[key], ...res.channels[key] }
        }
      })
    }
  } catch (error) {
    console.error('加载模板失败', error)
  }
}

const applyChannelTemplates = () => {
  Object.values(channelTemplates.value).forEach(channel => {
    Object.entries(channel).forEach(([key, value]) => {
      if (value) {
        config.value.env[key] = value
      }
    })
  })
  ElMessage.success('渠道配置已应用到当前配置')
}

const saveTemplatesToServer = async () => {
  try {
    const fullTemplates = {
      byok: templates.value,
      channels: channelTemplates.value
    }
    await configApi.saveTemplates(fullTemplates)
    ElMessage.success('模板保存成功')
  } catch (error) {
    ElMessage.error('保存模板失败: ' + error)
  }
}

onMounted(() => {
  loadGroups()
  loadInstances()
  loadTemplates()
  loadDefaultBundle()
  
  if (route.query.type === 'group' && route.query.id) {
    configType.value = 'group'
    selectedTarget.value = route.query.id
    loadConfig()
  } else if (route.query.type === 'instance' && route.query.id) {
    configType.value = 'instance'
    selectedTarget.value = route.query.id
    loadConfig()
  }
})

watch(() => config.value.openclaw, () => {
  if (activeTab.value !== 'openclaw') {
    syncJsonEditorFromConfig()
  }
}, { deep: true })

watch(activeTab, (newTab, oldTab) => {
  if (newTab === 'openclaw' && oldTab !== 'openclaw') {
    try {
      applyStructuredInputsToConfig()
      syncJsonEditorFromConfig()
    } catch {
      ElMessage.error('结构化配置中存在无法序列化的内容，请检查 Provider 或 Media 配置')
    }
  }

  if (oldTab === 'openclaw' && newTab !== 'openclaw') {
    try {
      syncConfigFromJsonEditor()
      syncJsonEditorFromConfig()
    } catch {
      activeTab.value = 'openclaw'
      ElMessage.error('openclaw.json 格式错误，请先修正再切换标签')
    }
  }
})
</script>

<style scoped>
.config {
  padding: 20px;
}

.editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.templates {
  max-height: 400px;
  overflow-y: auto;
}

.inner-tabs :deep(.el-tabs__content) {
  padding-top: 8px;
}

.provider-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.sub-card {
  margin-bottom: 12px;
}

.sub-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-note {
  margin-bottom: 12px;
  padding: 12px;
  background: #f5f7fa;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  color: #909399;
}

.form-tip {
  margin-top: 6px;
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.compare-container {
  padding: 10px;
}

.config-compare {
  max-height: 400px;
  overflow-y: auto;
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
}

.config-compare pre {
  margin: 0;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}

.diff-result {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px;
  border-radius: 4px;
}

.diff-result.success {
  background: #f0f9eb;
  color: #67c23a;
  border: 1px solid #e1f3d8;
}

.diff-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
</style>
