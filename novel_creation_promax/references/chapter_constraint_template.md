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

== 设定底座约束 ==
人物现实锚点：{character_reality_anchor}
地点与消费锚点：{location_and_cost_anchor}
势力行动边界：{faction_action_limits}
事件因果链：{event_causality_chain}
关系与信息差：{relationship_and_information_gap}
本章常识禁区：{common_sense_no_go}
违规后果：出现收入/住所/职业/技术/法律流程/信息差漂移时，本章退回重写。

== 真相文件 rule_stack ==
来源：`摘要/chapter_{N}_rule_stack.json` + `素材/chapter_{N}_truth_brief.md`
必须读取：characters/locations/factions/events/relationships/resources/foreshadowing 七类事实。
写作规则：
• 人物台词必须符合 speech_style；行为必须符合 behavior_rules；职业、收入、住处必须符合 reality_anchor。
• 地点必须符合 cost_level、access_rules、real_world_rules；不能随意进入有权限门槛的地点。
• 势力行动必须付出 action_boundary 中规定的理由、流程和代价。
• 事件推进必须承接 cause/effect/evidence_chain，不得凭空跳结论。
• 关系变化必须承接 trust_level、conflict、information_gap，不得突然知情或突然亲密。
• 资源和能力必须遵守 limits/cost，不能无代价万能解决。
写后规则：先审查 `素材/truth_delta_candidates_ch{N}.md`，再把本章新增事实写入 `摘要/chapter_{N}_truth_delta.json`。候选事实未审查、属实事实未写入、review_note 为空，post 都不通过。

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

== 时间距离约束（from AI_NovelGenerator）==
以下信息在近N章内已写过，本章避免重复展开：
- 近2章内（SKIP，不写）：{recent_2ch_skip_items}
- 近3-5章内（≥40%修改要求）：{recent_3to5ch_must_modify_items}
- 近6-10章内（可简略提及）：{recent_6to10ch_brief_items}
违规后果：重复展开已有信息 = 水字数，审计扣分。

== 隐喻环境约束（from AI_NovelGenerator）==
本章环境象征主题：{metaphor_theme}
环境描写必须服务叙事：{environment_narrative_purpose}
可用象征元素：{available_metaphor_elements}
禁止：纯风景铺陈、与情绪无关的环境描写。

== 去AI约束（Pass 2 重点）==
本章高危词：{high_risk_words_from_prev_audit}
速查卡 §七 三刀法则：本章重点"刀"哪几段：{three_cuts_focus}
