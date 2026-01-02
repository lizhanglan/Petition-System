import request from './request'

// 规则接口
export interface Rule {
  id: string
  name: string
  description: string
  type: string
  category: string
  enabled: boolean
  priority: number
  pattern?: string
  min_length?: number
  max_length?: number
  keywords?: string[]
}

// 规则性能接口
export interface RulePerformance {
  rule_id: string
  rule_name: string
  execution_count: number
  total_time: number
  average_time: number
  max_time: number
  min_time: number
  is_slow: boolean
}

// 规则统计接口
export interface RuleStatistics {
  total_rules: number
  enabled_rules: number
  disabled_rules: number
  rules_by_category: Record<string, number>
  rules_by_type: Record<string, number>
}

// 获取规则列表
export const getRulesList = () => {
  return request.get<Rule[]>('/admin/rules/list')
}

// 获取规则性能
export const getRulesPerformance = () => {
  return request.get<RulePerformance[]>('/admin/rules/performance')
}

// 获取规则统计
export const getRulesStatistics = () => {
  return request.get<RuleStatistics>('/admin/rules/statistics')
}

// 切换规则启用状态
export const toggleRule = (ruleId: string, enabled: boolean) => {
  return request.put(`/admin/rules/${ruleId}/toggle`, { enabled })
}

// 重载规则配置
export const reloadRules = () => {
  return request.post('/admin/rules/reload')
}
