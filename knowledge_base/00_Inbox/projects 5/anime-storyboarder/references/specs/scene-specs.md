# 场景生成规范

## 目录
- [核心原则](#核心原则)
- [双通道生成逻辑](#双通道生成逻辑)
- [白名单/黑名单机制](#白名单黑名单机制)
- [检查清单](#检查清单)
- [典型场景模板](#典型场景模板)

---

## 核心原则

**绝对禁止**：绘图指令中包含任何人物
**必须包含**：绘图指令必须是纯环境场景（empty/scenery only/no people）

---

## 双通道生成逻辑

```
场景信息
    ├─ 通道1：画面描述（中文）
    │   ├─ 可以提及人物活动（如"由于陆砚礼的剧痛挣扎"）
    │   ├─ 可以提及故事背景（如"暗示原本装在那里的暖玉已被强行抢走"）
    │   └─ 重点描述空间、光线、氛围
    │
    └─ 通道2：绘图指令（英文）
        ├─ 删除所有人物相关词汇（人名、人称、身体部位、动作、衣物）
        ├─ 强制添加：empty / scenery only / no people
        ├─ 只描述：空间结构、家具陈设、装饰物品、建筑元素、自然元素、光线效果、质感细节、环境氛围
        └─ 添加技术参数：8k, --ar 16:9, --v 6.0
```

### 通道1：画面描述（中文）
- 可以提及人物活动
- 可以提及故事背景
- 重点描述空间、光线、氛围

### 通道2：绘图指令（英文）
- 绝对禁止包含任何人相关的词汇
- 必须包含empty/scenery only/no people等关键词
- 只描述纯环境场景

---

## 白名单/黑名单机制

| 类别 | 白名单（允许） | 黑名单（禁止） |
|-----|---------------|---------------|
| 空间结构 | interior, exterior, room, hall, garden | - |
| 家具陈设 | table, chair, bed, cabinet | - |
| 装饰物品 | curtain, vase, painting, lantern | - |
| 建筑元素 | window, door, pillar, roof | - |
| 自然元素 | tree, flower, sky, moon, water | - |
| 光线效果 | candlelight, moonlight, shadow | - |
| 质感细节 | silk, wood, stone, fabric | - |
| 环境氛围 | festive, gloomy, peaceful | - |
| 人物相关 | - | man, woman, person, character, figure, human, people |
| 人物部位 | - | face, hand, body, head, foot, arm, leg, eye, ear, mouth, nose |
| 人物动作 | - | sitting, standing, walking, running, lying, sleeping, eating, drinking |
| 人物衣物 | - | dress, robe, coat, shirt, pants, shoes, hat, jewelry |
| 人物暗示 | - | silhouette, shadow of person, human figure in distance |

---

## 检查清单（11项）：

- [ ] 绘图指令包含关键词：empty / scenery only / no people / unoccupied
- [ ] 无任何人词汇：man, woman, person, character, figure等
- [ ] 无任何人部位：face, hand, body等
- [ ] 无任何人动作：sitting, standing, walking等
- [ ] 无任何人衣物：dress, robe, coat等
- [ ] 无任何人暗示：silhouette, shadow of person等
- [ ] 描述了场景的空间结构
- [ ] 描述了家具陈设和装饰物品
- [ ] 描述了光线效果和质感细节
- [ ] 描述了环境氛围
- [ ] 包含了技术参数（8k, --ar 16:9, --v 6.0）

---

## 典型场景模板

### 室内场景模板

```
Interior of a [空间类型], empty.
[家具陈设描述]
[装饰物品描述]
[光线效果描述]
[质感细节描述]
[环境氛围描述]
[技术参数] --ar 16:9 --v 6.0
```

**示例**：
```
Interior of a traditional Chinese study room, empty. A large desk in the center with ink stone and brushes. Bookshelves filled with ancient scrolls on both walls. A paper lamp hanging from the ceiling casting warm light. A wooden floor with tatami mats. The atmosphere is scholarly and peaceful. 8k, traditional Chinese aesthetics. --ar 16:9 --v 6.0
```

### 室外场景模板

```
[场景类型] in [地点], empty.
[自然元素描述]
[建筑元素描述]
[光线效果描述]
[环境氛围描述]
[技术参数] --ar 16:9 --v 6.0
```

**示例**：
```
A traditional Chinese courtyard in autumn, empty. Red maple leaves falling on the stone ground. A small pavilion in the center with a round table. Trees with golden leaves surrounding the courtyard. Soft afternoon sunlight casting long shadows. The atmosphere is nostalgic and peaceful. 8k, hyper-realistic foliage. --ar 16:9 --v 6.0
```

### 回忆场景模板

```
[场景描述], empty.
[时光滤镜描述]
[关键物品描述]
[环境细节描述]
[怀旧氛围描述]
[技术参数] --ar 16:9 --v 6.0
```

**示例**：
```
A childhood bedroom, empty. Soft nostalgic lighting with warm tones. A small wooden bed with a teddy bear. Toys scattered on the floor. A window showing a sunny day outside. The atmosphere is dreamy and full of memories. 8k, soft focus. --ar 16:9 --v 6.0
```
