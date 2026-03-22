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
              <div class="editor-container">
                <codemirror
                  v-model="openclawJsonStr"
                  placeholder='{"tools": {...}}'
                  :style="{ height: '500px' }"
                  :autofocus="true"
                  :indent-with-tab="true"
                  :tab-size="2"
                  :extensions="editorExtensions"
                />
              </div>
              <div style="margin-top: 10px;">
                <el-button @click="formatJson">格式化 JSON</el-button>
                <el-button @click="validateJson">验证 JSON</el-button>
                <el-button type="warning" @click="restoreDefaultConfig">恢复默认</el-button>
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

            <el-tab-pane label="安全策略" name="security">
              <el-form label-width="200px">
                <el-divider>Gateway 设置</el-divider>
                <el-form-item label="绑定模式">
                  <el-select v-model="config.openclaw.gateway.bind">
                    <el-option label="auto (自动)" value="auto" />
                    <el-option label="loopback (仅本地)" value="loopback" />
                    <el-option label="lan (局域网)" value="lan" />
                    <el-option label="tailnet (Tailscale)" value="tailnet" />
                    <el-option label="custom (自定义)" value="custom" />
                  </el-select>
                </el-form-item>
                <el-form-item label="Gateway 端口">
                  <el-input-number v-model="config.openclaw.gateway.port" :min="1" :max="65535" />
                </el-form-item>
                <el-form-item label="允许的Origins" v-if="config.openclaw.gateway.bind === 'lan'">
                  <el-input v-model="config.env.OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS" placeholder="* 或 http://192.168.1.100:18789" />
                  <div class="form-tip">局域网模式下建议设置为 * 或具体的IP地址，多个用逗号分隔</div>
                </el-form-item>

                <el-divider>终端执行 (exec)</el-divider>
                <el-form-item label="安全模式">
                  <el-select v-model="config.openclaw.tools.exec.security">
                    <el-option label="full - 完全放开" value="full" />
                    <el-option label="policies - 审批模式" value="policies" />
                    <el-option label="local - 本地模式" value="local" />
                  </el-select>
                </el-form-item>
                <el-form-item label="允许宿主机执行">
                  <el-switch v-model="config.openclaw.tools.exec.host" true-value="gateway" false-value="sandbox" />
                </el-form-item>


                <el-divider>网页获取 (web)</el-divider>
                <el-form-item label="启用网页获取">
                  <el-switch :model-value="!!config.openclaw.tools.web.fetch" @update:model-value="v => config.openclaw.tools.web.fetch = v ? {} : undefined" />
                </el-form-item>

              </el-form>
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
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
const activeTemplates = ref(['openai'])
const activeChannelTemplates = ref(['telegram'])

const groups = ref([])
const instances = ref([])

const templates = ref({
  openai: { OPENAI_API_KEY: '' },
  anthropic: { ANTHROPIC_API_KEY: '' },
  google: { GEMINI_API_KEY: '' },
  deepseek: { DEEPSEEK_API_KEY: '' },
  minimax: { MINIMAX_API_KEY: '' },
  ollama: { OLLAMA_API_KEY: '' },
  openrouter: { OPENROUTER_API_KEY: '' },
  huggingface: { HUGGINGFACE_HUB_TOKEN: '' },
  groq: { GROQ_API_KEY: '' },
  xai: { XAI_API_KEY: '' },
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
  discord: { DISCORD_BOT_TOKEN: '' },
  feishu: { FEISHU_APP_ID: '', FEISHU_APP_SECRET: '' },
  slack: { SLACK_BOT_TOKEN: '', SLACK_APP_TOKEN: '' },
  signal: { SIGNAL_PHONE_NUMBER: '' }
})

const config = ref({
  env: {
    OPENCLAW_HOME: '/root',
    OPENCLAW_GATEWAY_PORT: '18789',
    OPENCLAW_STATE_DIR: '/root/.openclaw',
    OPENCLAW_DISABLE_BONJOUR: '1',
    OPENCLAW_GATEWAY_CONTROL_UI_ALLOWED_ORIGINS: '*'
  },
  openclaw: {
    tools: {
      exec: { backgroundMs: 10000, timeoutSec: 1800, notifyOnExit: true },
      web: { fetch: { enabled: true } }
    },
    gateway: { bind: 'lan', port: 18789 }
  }
})

const openclawJsonStr = ref('')

const defaultTemplate = ref({
  tools: {
    exec: { backgroundMs: 10000, timeoutSec: 1800, notifyOnExit: true },
    web: { fetch: { enabled: true } }
  },
  gateway: { bind: 'lan', port: 18789 }
})

const currentConfigCompare = ref({})
const configDiffs = ref([])

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
    let configData
    if (configType.value === 'instance') {
      configData = await instanceApi.getConfig(selectedTarget.value)
    } else {
      configData = await groupApi.getConfig(selectedTarget.value)
    }

    config.value.env = { ...config.value.env, ...configData.env }
    config.value.openclaw = { ...config.value.openclaw, ...configData.openclaw }
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
    // Sync JSON string to object before saving
    try {
      if (openclawJsonStr.value) {
        config.value.openclaw = JSON.parse(openclawJsonStr.value)
      }
    } catch (e) {
      activeTab.value = 'openclaw'
      ElMessage.error('openclaw.json 格式错误，请检查并修正后再保存')
      return
    }

    const data = {
      env_vars: config.value.env,
      openclaw_json: config.value.openclaw
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
    const obj = JSON.parse(openclawJsonStr.value)
    openclawJsonStr.value = JSON.stringify(obj, null, 2)
    config.value.openclaw = obj
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
    JSON.parse(openclawJsonStr.value)
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
