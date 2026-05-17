# 每章约束注入模板

> 写前自动填充，直接注入写作 prompt。替代手动"约束组装"过程。
> 填充规则：`{占位符}` 从对应来源读取数据替换。

---

【第{N}章 写中约束】

== 红线（写作宪法已加载，此处仅列本章高危项）==
• 本章字数目标：{word_count_range}
• 截断点：{chapter_cutoff_event}
• 标题关键词：{title_keywords}

== 人物约束 ==
• {character_A_name}：矛盾特质={contradictory_traits}，行为指纹={behavioral_fingerprint}
  本章负面约束：{negative_constraints}
• {character_B_name}：矛盾特质={contradictory_traits}，行为指纹={behavioral_fingerprint}
  本章负面约束：{negative_constraints}

== 对话约束 ==
本章对话场景类型：{dialogue_scene_type}
适用技法：{dialogue_techniques}
声纹要求：{voice_requirements}

== 节奏约束 ==
本章类型：{chapter_rhythm_type}
爽点设计：{climax_design}
情绪曲线：期待({tension_expect}) → 压制({tension_suppress}) → 反转({tension_reverse}) → 释放({tension_release})

== 题材约束（从 .profile.yaml 加载）==
字数范围：{genre_word_count_min}-{genre_word_count_max}
开头钩子字数上限：{genre_opening_hook_chars}字内必须有冲突
高潮位置：章节{genre_climax_at_percent}%处
爽:压比例：{genre_cool_to_pressure_ratio}
对话占比目标：{genre_dialogue_target}%
主strand断档上限：≤{genre_strand_gap}章
偏好爽点模式：{genre_preferred_cool_types}
偏好钩子类型：{genre_preferred_hook_types}

== 追读力约束（from reading-power-taxonomy.md）==
本章钩子类型（H1-H6）：{planned_hook_type}
本章爽点模式（C1-C8）：{planned_cool_point_mode}
本章微兑现（M1-M7）：{planned_micro_payoffs}
当前未回收债务数：{open_debt_count}（≤3安全，>3必须本章回收至少1个）

== 债务状态（from override-debt-system.md）==
当前open合同数：{open_contract_count}/3
需本章处理的合同：{contracts_due_this_chapter}
债务升级预警：{debt_escalation_warnings}

== 去AI约束（Pass 2 重点）==
本章高危词：{high_risk_words_from_prev_audit}
速查卡 §七 三刀法则：本章重点"刀"哪几段：{three_cuts_focus}
