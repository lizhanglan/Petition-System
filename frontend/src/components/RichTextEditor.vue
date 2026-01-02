<template>
  <div class="rich-text-editor">
    <div class="editor-toolbar">
      <div class="toolbar-group">
        <button @click="execCommand('bold')" title="粗体" class="toolbar-btn">
          <strong>B</strong>
        </button>
        <button @click="execCommand('italic')" title="斜体" class="toolbar-btn">
          <em>I</em>
        </button>
        <button @click="execCommand('underline')" title="下划线" class="toolbar-btn">
          <u>U</u>
        </button>
        <button @click="execCommand('strikeThrough')" title="删除线" class="toolbar-btn">
          <s>S</s>
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <select @change="changeFontSize" class="toolbar-select" title="字号">
          <option value="">字号</option>
          <option value="1">小</option>
          <option value="3">正常</option>
          <option value="5">大</option>
          <option value="7">特大</option>
        </select>
        
        <select @change="changeHeading" class="toolbar-select" title="标题">
          <option value="">正文</option>
          <option value="h1">标题 1</option>
          <option value="h2">标题 2</option>
          <option value="h3">标题 3</option>
        </select>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <button @click="execCommand('justifyLeft')" title="左对齐" class="toolbar-btn">
          ≡
        </button>
        <button @click="execCommand('justifyCenter')" title="居中" class="toolbar-btn">
          ≡
        </button>
        <button @click="execCommand('justifyRight')" title="右对齐" class="toolbar-btn">
          ≡
        </button>
        <button @click="execCommand('justifyFull')" title="两端对齐" class="toolbar-btn">
          ≡
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <button @click="execCommand('insertUnorderedList')" title="无序列表" class="toolbar-btn">
          ☰
        </button>
        <button @click="execCommand('insertOrderedList')" title="有序列表" class="toolbar-btn">
          ≣
        </button>
        <button @click="execCommand('indent')" title="增加缩进" class="toolbar-btn">
          →
        </button>
        <button @click="execCommand('outdent')" title="减少缩进" class="toolbar-btn">
          ←
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <input 
          type="color" 
          @change="changeColor" 
          title="文字颜色" 
          class="toolbar-color"
        />
        <input 
          type="color" 
          @change="changeBackgroundColor" 
          title="背景颜色" 
          class="toolbar-color"
        />
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <button @click="insertTable" title="插入表格" class="toolbar-btn">
          ⊞
        </button>
        <button @click="insertLink" title="插入链接" class="toolbar-btn">
          🔗
        </button>
        <button @click="insertImage" title="插入图片" class="toolbar-btn">
          🖼
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <button @click="undo" title="撤销" class="toolbar-btn">
          ↶
        </button>
        <button @click="redo" title="重做" class="toolbar-btn">
          ↷
        </button>
      </div>
      
      <div class="toolbar-divider"></div>
      
      <div class="toolbar-group">
        <button @click="clearFormat" title="清除格式" class="toolbar-btn">
          ✕
        </button>
      </div>
    </div>
    
    <div 
      ref="editorRef"
      class="editor-content"
      contenteditable="true"
      @input="handleInput"
      @paste="handlePaste"
    ></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessageBox } from 'element-plus'

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = ref<HTMLDivElement>()

onMounted(() => {
  if (editorRef.value && props.modelValue) {
    editorRef.value.innerHTML = props.modelValue
  }
})

watch(() => props.modelValue, (newValue) => {
  if (editorRef.value && editorRef.value.innerHTML !== newValue) {
    editorRef.value.innerHTML = newValue
  }
})

const handleInput = () => {
  if (editorRef.value) {
    emit('update:modelValue', editorRef.value.innerHTML)
  }
}

const handlePaste = (e: ClipboardEvent) => {
  e.preventDefault()
  const text = e.clipboardData?.getData('text/plain')
  if (text) {
    document.execCommand('insertText', false, text)
  }
}

const execCommand = (command: string, value?: string) => {
  document.execCommand(command, false, value)
  editorRef.value?.focus()
}

const changeFontSize = (e: Event) => {
  const target = e.target as HTMLSelectElement
  if (target.value) {
    execCommand('fontSize', target.value)
    target.value = ''
  }
}

const changeHeading = (e: Event) => {
  const target = e.target as HTMLSelectElement
  if (target.value) {
    execCommand('formatBlock', target.value)
    target.value = ''
  }
}

const changeColor = (e: Event) => {
  const target = e.target as HTMLInputElement
  execCommand('foreColor', target.value)
}

const changeBackgroundColor = (e: Event) => {
  const target = e.target as HTMLInputElement
  execCommand('backColor', target.value)
}

const insertTable = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入表格尺寸（例如：3x3）', '插入表格', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPattern: /^\d+x\d+$/,
      inputErrorMessage: '格式错误，请输入如 3x3'
    })
    
    if (value) {
      const parts = value.split('x').map(Number)
      const rows = parts[0] || 3
      const cols = parts[1] || 3
      let tableHTML = '<table border="1" style="border-collapse: collapse; width: 100%;">'
      
      for (let i = 0; i < rows; i++) {
        tableHTML += '<tr>'
        for (let j = 0; j < cols; j++) {
          tableHTML += '<td style="padding: 8px; border: 1px solid #ddd;">&nbsp;</td>'
        }
        tableHTML += '</tr>'
      }
      tableHTML += '</table><p><br></p>'
      
      execCommand('insertHTML', tableHTML)
    }
  } catch {
    // 用户取消
  }
}

const insertLink = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入链接地址', '插入链接', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: 'https://example.com'
    })
    
    if (value) {
      execCommand('createLink', value)
    }
  } catch {
    // 用户取消
  }
}

const insertImage = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入图片地址', '插入图片', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: 'https://example.com/image.jpg'
    })
    
    if (value) {
      execCommand('insertImage', value)
    }
  } catch {
    // 用户取消
  }
}

const undo = () => {
  execCommand('undo')
}

const redo = () => {
  execCommand('redo')
}

const clearFormat = () => {
  execCommand('removeFormat')
}

// 暴露方法供父组件使用
defineExpose({
  getContent: () => editorRef.value?.innerHTML || '',
  setContent: (html: string) => {
    if (editorRef.value) {
      editorRef.value.innerHTML = html
    }
  },
  clear: () => {
    if (editorRef.value) {
      editorRef.value.innerHTML = ''
    }
  }
})
</script>

<style scoped>
.rich-text-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
}

.editor-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding: 8px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
}

.toolbar-group {
  display: flex;
  gap: 4px;
  align-items: center;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background-color: #dcdfe6;
  margin: 0 4px;
}

.toolbar-btn {
  min-width: 32px;
  height: 32px;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.toolbar-btn:hover {
  background-color: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.toolbar-btn:active {
  background-color: #409eff;
  color: white;
}

.toolbar-select {
  height: 32px;
  padding: 4px 8px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  background-color: white;
  cursor: pointer;
  font-size: 14px;
}

.toolbar-select:hover {
  border-color: #409eff;
}

.toolbar-color {
  width: 32px;
  height: 32px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
}

.toolbar-color:hover {
  border-color: #409eff;
}

.editor-content {
  min-height: 400px;
  max-height: 600px;
  padding: 20px;
  overflow-y: auto;
  background-color: white;
  font-size: 14px;
  line-height: 1.8;
  outline: none;
}

.editor-content:focus {
  outline: none;
}

/* 编辑器内容样式 */
.editor-content :deep(h1) {
  font-size: 28px;
  font-weight: bold;
  margin: 16px 0;
}

.editor-content :deep(h2) {
  font-size: 24px;
  font-weight: bold;
  margin: 14px 0;
}

.editor-content :deep(h3) {
  font-size: 20px;
  font-weight: bold;
  margin: 12px 0;
}

.editor-content :deep(p) {
  margin: 8px 0;
}

.editor-content :deep(ul),
.editor-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.editor-content :deep(li) {
  margin: 4px 0;
}

.editor-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.editor-content :deep(table td),
.editor-content :deep(table th) {
  border: 1px solid #ddd;
  padding: 8px;
}

.editor-content :deep(img) {
  max-width: 100%;
  height: auto;
  margin: 12px 0;
}

.editor-content :deep(a) {
  color: #409eff;
  text-decoration: underline;
}
</style>
