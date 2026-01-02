"""
初始化标准信访模板
预置 12 类标准信访文书模板
"""
import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv()

# 12 类标准信访文书模板
STANDARD_TEMPLATES = [
    {
        "name": "信访事项受理通知书",
        "document_type": "acceptance_notice",
        "structure": {
            "sections": ["标题", "受理编号", "受理内容", "办理时限", "落款"],
            "required_fields": ["petitioner_name", "petition_number", "acceptance_date"]
        },
        "content_template": """信访事项受理通知书

受理编号：{{petition_number}}

{{petitioner_name}}：

您于{{petition_date}}提出的信访事项，我单位已于{{acceptance_date}}受理。根据《信访工作条例》规定，我们将在{{deadline}}前办结并答复。

特此通知。

{{department}}
{{signature_date}}""",
        "fields": {
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "acceptance_date": {"name": "受理日期", "type": "date", "required": True},
            "deadline": {"name": "办结期限", "type": "text", "required": True},
            "department": {"name": "受理单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项不予受理通知书",
        "document_type": "rejection_notice",
        "structure": {
            "sections": ["标题", "编号", "不予受理原因", "救济途径", "落款"],
            "required_fields": ["petitioner_name", "petition_number", "rejection_reason"]
        },
        "content_template": """信访事项不予受理通知书

编号：{{petition_number}}

{{petitioner_name}}：

您于{{petition_date}}提出的信访事项，经审查，根据《信访工作条例》第{{article}}条规定，决定不予受理。

不予受理原因：
{{rejection_reason}}

如对本决定不服，您可以：
{{remedy_path}}

特此通知。

{{department}}
{{signature_date}}""",
        "fields": {
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "article": {"name": "条款编号", "type": "text", "required": True},
            "rejection_reason": {"name": "不予受理原因", "type": "text", "required": True},
            "remedy_path": {"name": "救济途径", "type": "text", "required": True},
            "department": {"name": "受理单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项转办单",
        "document_type": "transfer_letter",
        "structure": {
            "sections": ["标题", "转办编号", "转办内容", "办理要求", "落款"],
            "required_fields": ["petition_number", "transfer_to", "transfer_reason"]
        },
        "content_template": """信访事项转办单

转办编号：{{transfer_number}}

{{transfer_to}}：

现将{{petitioner_name}}于{{petition_date}}提出的信访事项转交你单位办理。

信访事项概要：
{{petition_summary}}

转办理由：
{{transfer_reason}}

办理要求：
1. 请于{{deadline}}前办结并书面答复信访人；
2. 办结后将处理结果报送我单位备案。

{{department}}
{{signature_date}}""",
        "fields": {
            "transfer_number": {"name": "转办编号", "type": "text", "required": True},
            "transfer_to": {"name": "承办单位", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "petition_summary": {"name": "信访事项概要", "type": "text", "required": True},
            "transfer_reason": {"name": "转办理由", "type": "text", "required": True},
            "deadline": {"name": "办结期限", "type": "text", "required": True},
            "department": {"name": "转办单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项答复意见书",
        "document_type": "reply_letter",
        "structure": {
            "sections": ["标题", "答复编号", "信访事项", "调查情况", "处理意见", "落款"],
            "required_fields": ["petitioner_name", "petition_number", "reply_content"]
        },
        "content_template": """信访事项答复意见书

答复编号：{{reply_number}}

{{petitioner_name}}：

您于{{petition_date}}提出的信访事项（编号：{{petition_number}}），我单位已办理完毕，现答复如下：

一、信访事项
{{petition_content}}

二、调查情况
{{investigation}}

三、处理意见
{{reply_content}}

如对本答复意见不服，您可以自收到本答复意见之日起30日内向{{appeal_department}}提出复查申请。

{{department}}
{{signature_date}}""",
        "fields": {
            "reply_number": {"name": "答复编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "petition_content": {"name": "信访事项", "type": "text", "required": True},
            "investigation": {"name": "调查情况", "type": "text", "required": True},
            "reply_content": {"name": "处理意见", "type": "text", "required": True},
            "appeal_department": {"name": "复查单位", "type": "text", "required": False},
            "department": {"name": "答复单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项复查意见书",
        "document_type": "review_opinion",
        "structure": {
            "sections": ["标题", "复查编号", "原处理意见", "复查情况", "复查结论", "落款"],
            "required_fields": ["petitioner_name", "original_reply", "review_conclusion"]
        },
        "content_template": """信访事项复查意见书

复查编号：{{review_number}}

{{petitioner_name}}：

您对{{original_department}}作出的{{original_reply_number}}号答复意见不服，申请复查。经复查，现提出如下意见：

一、原处理意见
{{original_reply}}

二、复查情况
{{review_investigation}}

三、复查结论
{{review_conclusion}}

如对本复查意见不服，您可以自收到本复查意见之日起30日内向{{appeal_department}}提出复核申请。

{{department}}
{{signature_date}}""",
        "fields": {
            "review_number": {"name": "复查编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "original_department": {"name": "原答复单位", "type": "text", "required": True},
            "original_reply_number": {"name": "原答复编号", "type": "text", "required": True},
            "original_reply": {"name": "原处理意见", "type": "text", "required": True},
            "review_investigation": {"name": "复查情况", "type": "text", "required": True},
            "review_conclusion": {"name": "复查结论", "type": "text", "required": True},
            "appeal_department": {"name": "复核单位", "type": "text", "required": False},
            "department": {"name": "复查单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项督办通知书",
        "document_type": "supervision_notice",
        "structure": {
            "sections": ["标题", "督办编号", "督办事项", "督办要求", "落款"],
            "required_fields": ["supervised_department", "petition_number", "supervision_requirements"]
        },
        "content_template": """信访事项督办通知书

督办编号：{{supervision_number}}

{{supervised_department}}：

{{petitioner_name}}于{{petition_date}}提出的信访事项（编号：{{petition_number}}），已超过办理期限，现予以督办。

督办要求：
{{supervision_requirements}}

请于{{new_deadline}}前办结并报送办理结果。

{{department}}
{{signature_date}}""",
        "fields": {
            "supervision_number": {"name": "督办编号", "type": "text", "required": True},
            "supervised_department": {"name": "被督办单位", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "supervision_requirements": {"name": "督办要求", "type": "text", "required": True},
            "new_deadline": {"name": "新办结期限", "type": "text", "required": True},
            "department": {"name": "督办单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项办结报告",
        "document_type": "completion_report",
        "structure": {
            "sections": ["标题", "报告编号", "办理过程", "办理结果", "落款"],
            "required_fields": ["petition_number", "handling_process", "handling_result"]
        },
        "content_template": """信访事项办结报告

报告编号：{{report_number}}

关于{{petitioner_name}}信访事项（编号：{{petition_number}}）的办理情况报告如下：

一、信访事项概要
{{petition_summary}}

二、办理过程
{{handling_process}}

三、办理结果
{{handling_result}}

四、信访人意见
{{petitioner_feedback}}

该信访事项已于{{completion_date}}办结。

{{department}}
{{signature_date}}""",
        "fields": {
            "report_number": {"name": "报告编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "petition_summary": {"name": "信访事项概要", "type": "text", "required": True},
            "handling_process": {"name": "办理过程", "type": "text", "required": True},
            "handling_result": {"name": "办理结果", "type": "text", "required": True},
            "petitioner_feedback": {"name": "信访人意见", "type": "text", "required": False},
            "completion_date": {"name": "办结日期", "type": "date", "required": True},
            "department": {"name": "办理单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项延期办理申请书",
        "document_type": "extension_application",
        "structure": {
            "sections": ["标题", "申请编号", "延期理由", "新办结期限", "落款"],
            "required_fields": ["petition_number", "extension_reason", "new_deadline"]
        },
        "content_template": """信访事项延期办理申请书

申请编号：{{application_number}}

{{superior_department}}：

{{petitioner_name}}于{{petition_date}}提出的信访事项（编号：{{petition_number}}），原定于{{original_deadline}}办结。因以下原因，申请延期办理：

延期理由：
{{extension_reason}}

申请将办结期限延长至{{new_deadline}}。

特此申请，请予批准。

{{department}}
{{signature_date}}""",
        "fields": {
            "application_number": {"name": "申请编号", "type": "text", "required": True},
            "superior_department": {"name": "上级单位", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "original_deadline": {"name": "原办结期限", "type": "text", "required": True},
            "extension_reason": {"name": "延期理由", "type": "text", "required": True},
            "new_deadline": {"name": "新办结期限", "type": "text", "required": True},
            "department": {"name": "申请单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项终结通知书",
        "document_type": "termination_notice",
        "structure": {
            "sections": ["标题", "终结编号", "终结理由", "救济途径", "落款"],
            "required_fields": ["petition_number", "termination_reason"]
        },
        "content_template": """信访事项终结通知书

终结编号：{{termination_number}}

{{petitioner_name}}：

您提出的信访事项（编号：{{petition_number}}），根据《信访工作条例》第{{article}}条规定，决定终结办理。

终结理由：
{{termination_reason}}

如对本决定不服，您可以依法向人民法院提起诉讼。

特此通知。

{{department}}
{{signature_date}}""",
        "fields": {
            "termination_number": {"name": "终结编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "article": {"name": "条款编号", "type": "text", "required": True},
            "termination_reason": {"name": "终结理由", "type": "text", "required": True},
            "department": {"name": "终结单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项协调会议纪要",
        "document_type": "coordination_minutes",
        "structure": {
            "sections": ["标题", "会议编号", "参会单位", "会议内容", "协调意见", "落款"],
            "required_fields": ["meeting_date", "participants", "coordination_opinion"]
        },
        "content_template": """信访事项协调会议纪要

会议编号：{{meeting_number}}

会议时间：{{meeting_date}}
会议地点：{{meeting_location}}
主持人：{{moderator}}
参会单位：{{participants}}

会议议题：
关于{{petitioner_name}}信访事项（编号：{{petition_number}}）的协调处理

会议内容：
{{meeting_content}}

协调意见：
{{coordination_opinion}}

{{department}}
{{signature_date}}""",
        "fields": {
            "meeting_number": {"name": "会议编号", "type": "text", "required": True},
            "meeting_date": {"name": "会议时间", "type": "datetime", "required": True},
            "meeting_location": {"name": "会议地点", "type": "text", "required": True},
            "moderator": {"name": "主持人", "type": "text", "required": True},
            "participants": {"name": "参会单位", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "meeting_content": {"name": "会议内容", "type": "text", "required": True},
            "coordination_opinion": {"name": "协调意见", "type": "text", "required": True},
            "department": {"name": "组织单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项听证通知书",
        "document_type": "hearing_notice",
        "structure": {
            "sections": ["标题", "听证编号", "听证事项", "听证安排", "落款"],
            "required_fields": ["petition_number", "hearing_date", "hearing_location"]
        },
        "content_template": """信访事项听证通知书

听证编号：{{hearing_number}}

{{petitioner_name}}：

您提出的信访事项（编号：{{petition_number}}），经研究决定举行听证。现将有关事项通知如下：

一、听证事项
{{hearing_matter}}

二、听证时间
{{hearing_date}}

三、听证地点
{{hearing_location}}

四、听证人员
主持人：{{moderator}}
听证员：{{hearing_officers}}

五、注意事项
{{notes}}

请按时参加听证。如有特殊情况不能参加，请提前3日书面说明理由。

{{department}}
{{signature_date}}""",
        "fields": {
            "hearing_number": {"name": "听证编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "hearing_matter": {"name": "听证事项", "type": "text", "required": True},
            "hearing_date": {"name": "听证时间", "type": "datetime", "required": True},
            "hearing_location": {"name": "听证地点", "type": "text", "required": True},
            "moderator": {"name": "主持人", "type": "text", "required": True},
            "hearing_officers": {"name": "听证员", "type": "text", "required": True},
            "notes": {"name": "注意事项", "type": "text", "required": False},
            "department": {"name": "组织单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    },
    {
        "name": "信访事项调查报告",
        "document_type": "investigation_report",
        "structure": {
            "sections": ["标题", "报告编号", "调查背景", "调查过程", "调查结论", "处理建议", "落款"],
            "required_fields": ["petition_number", "investigation_process", "investigation_conclusion"]
        },
        "content_template": """信访事项调查报告

报告编号：{{report_number}}

一、调查背景
{{petitioner_name}}于{{petition_date}}提出信访事项（编号：{{petition_number}}），反映：
{{petition_content}}

二、调查过程
{{investigation_process}}

三、调查结论
{{investigation_conclusion}}

四、处理建议
{{handling_suggestion}}

{{department}}
{{signature_date}}""",
        "fields": {
            "report_number": {"name": "报告编号", "type": "text", "required": True},
            "petitioner_name": {"name": "信访人姓名", "type": "text", "required": True},
            "petition_date": {"name": "信访日期", "type": "date", "required": True},
            "petition_number": {"name": "信访编号", "type": "text", "required": True},
            "petition_content": {"name": "信访内容", "type": "text", "required": True},
            "investigation_process": {"name": "调查过程", "type": "text", "required": True},
            "investigation_conclusion": {"name": "调查结论", "type": "text", "required": True},
            "handling_suggestion": {"name": "处理建议", "type": "text", "required": True},
            "department": {"name": "调查单位", "type": "text", "required": True},
            "signature_date": {"name": "签发日期", "type": "date", "required": True}
        }
    }
]

def init_templates():
    """初始化标准模板"""
    # 连接数据库
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        database=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD')
    )
    
    try:
        cursor = conn.cursor()
        
        # 获取系统管理员用户 ID（假设 ID 为 1）
        cursor.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        result = cursor.fetchone()
        if not result:
            print("❌ 未找到用户，请先创建用户")
            return
        
        admin_user_id = result[0]
        print(f"✓ 使用用户 ID: {admin_user_id}")
        
        # 插入模板
        inserted_count = 0
        for template in STANDARD_TEMPLATES:
            # 检查模板是否已存在
            cursor.execute(
                "SELECT id FROM templates WHERE name = %s AND user_id = %s",
                (template['name'], admin_user_id)
            )
            
            if cursor.fetchone():
                print(f"  - 跳过已存在的模板: {template['name']}")
                continue
            
            # 插入模板
            cursor.execute("""
                INSERT INTO templates (
                    user_id, name, document_type, structure, 
                    content_template, fields, is_active, version
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                admin_user_id,
                template['name'],
                template['document_type'],
                json.dumps(template['structure'], ensure_ascii=False),
                template['content_template'],
                json.dumps(template['fields'], ensure_ascii=False),
                True,
                1
            ))
            
            inserted_count += 1
            print(f"  ✓ 已添加模板: {template['name']}")
        
        conn.commit()
        print(f"\n✓ 成功添加 {inserted_count} 个标准模板")
        print(f"✓ 总计 {len(STANDARD_TEMPLATES)} 个标准模板")
        
        cursor.close()
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("初始化标准信访文书模板")
    print("=" * 50)
    init_templates()
    print("=" * 50)
    print("完成！")
