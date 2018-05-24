# Dinodon

Dinodon 是一个静态 python 代码风格检查工具(毕不了业的毕业设计), 规则基本上基于 [PEP8](https://www.python.org/dev/peps/pep-0008/)

使用环境: Python3 + Command Line

#### 命名由来

Dinodon(链蛇属). 无毒, 温和, 可以当做宠物饲养. 怀着把 python 变成 dinodon 的想法写了这个库

#### 使用方法

目前没有通过包管理工具发布, 可以 clone 下 master/tag 1.0 版本进行试用

// 可以通过 --help 参数来查看使用说明

**0.自检 self-check**

一个没什么用的功能, 在开发的时候想着开发一个代码风格检查工具, 在开发迭代中不断进行自我检查并修改, 这就形成了一个有趣的循环

```shell
$ python3 dinodon.py self-check
```

 这个命令单纯去监测 dinodon.py 是否符合现有的规则

**1.检测文件 run**

输入文件名, 开始对其进行代码风格的检测(本路径下的 demo.py 内容与 dinodon.py 一致, 但手动添加了一些不符合规范的地方)

```shell
$ python3 dinodon.py run demo.py
```

结果输出如下:

```log
Error: line 1, column 0 <Multiple import in one line>
Error: line 200, column 0 <Blank line contains whitespace>
Warning: line 202, column 12 <Use lambda in high order function>
Error: line 401, column 0 <Expected 2 blank lines, found 1>
Warning: line 475, column 24 <Wrong format naming>
```

**1.1.使用插件 --plugins**

因为用 Python 编写, dinodon 借动态引入有着不错的扩展性. 添加扩展的方法也很简单, 通过 `--plugins=file` 的格式将扩展文件中的检查规则导入即可

```shell
$ python3 dinodon.py run --plugins=dinodon-plugin.py demo.py
```

**1.2.生成报告 --report**

当检测完后可以生成一份报告, 无论是用来算 KPI , 喷人还是学习都很方便

```shell
$ python3 dinodon.py run --report demo.py
```

生成的 report 的样例参考 [Report](https://bewils.github.io/Dinodon/)

分为 Overall, Statistics, Details 三部分, 前两部分是总体上的统计数据, Details 中记录了每个不规范处的内容, 点开后可以看到该处的代码

**1.3.检查开关**

这个功能是向 [SwiftLint](https://github.com/realm/SwiftLint) 学过来的, 有些特殊情况(比如数据是 hard code)时, 过分考虑规范只会强行增加代码复杂性, 因此给了开关可以绕过这些地方

使用方法 `# dinodon:disable/enable xxx`

```Python
# dinodon:disable check_naming
aCamelNaming = "hhhhhhhh"
# dinodon:enable check_naming
anotherCamelNaming = "hhhhhhhh"
```

这种情况下 `aCamelNaming` 不会被检测, `anotherCamelNaming` 则会检测出不合规范

#### 核心检查

核心检查部分分为三大类: 对 physical_line, logical_line 和 ast 的检查

1. physical_line: 物理意义上的一行, 单纯在字符串的层面来考虑, 比如行内是否用 tab 来缩进
2. logical_line: 逻辑意义上的一行, 包括与上下行之间的关系, 以及行内格式的规范, 比如导入多个模块每个模块都要换行
3. ast: 抽象语法树检查, 通过遍历整棵树来对整体或局部进行检查, 比如对命名的检查

其实对 logical_line 和 ast 检查的分界并不是那么明显, 最后对外都是一样的接口, 只是内部实现怎样方便就怎样即可.

比如对命名的检查也可以直接遍历每一行来判断, 而通过遍历 ast 的话可以简化判断:

* 赋值语句左值命名是否规范
* 方法定义命名是否规范
* 类定义命名是否规范

基于一个假设: 如果定义都符合规范那么使用时一定符合规范

在这种情况下通过 ast 来检查就很方便

**扩展编写**

针对上面三种检查方式编写扩展的方法其实很简单, 按照 dinodon-plugin.py 中的样例, 将扩展的检查方法通过 plugins 导出来即可, 检查方法编写规则如下:

```python
# 推荐以 check_xxx 命名
# 传入改行字符串和行号
def check_physical_line_function(physical_line, line_number)
# 传入该行字符串, 行号和一个全局的通用字典(用来保存上下文信息)
def check_logical_line_function(logical_line, line_number, extarParams)
# 传入当前节点, 行号等信息可以用 node 中获取
def check_ast_function(node)

# 通用返回值格式 tuple or [tuple]
# (Level: ViolationLevel, 
#	Type: ViolationType,
#   Line info: (line_number: int, offset: int),
#   Description: str)
```

#### 结果数据

在开启 `--report` 选项后实际上最后的检测结果会导出到 `report.js` 中, 可以自行使用该文件中的数据, 目前的 report 只是一个利用这个数据做的前端界面而已

#### 写在最后

第一次用 python 来一个完整的项目, 写到最后代码真是惨不忍睹, 明明自己代码写得这么烂还写了个工具来检查别人的代码质量(笑).

代码量不是很大, 功能却还蛮多, 设计整个的结构也花了不少时间. 主要参考了 [pycodestyle](https://github.com/PyCQA/pycodestyle) 和 [SwiftLint](https://github.com/realm/SwiftLint). 相比于这两个大家伙无从下手, 通过 dinodon 这个小玩具来了解 lint 工具的设计和实现还是很有趣的.

通过编写 dinodon 还证明了一个事情, 就算代码可以全部通过代码分析工具的检查, 还是可以写得这么烂可读性这么差(没有大规模使用说不定还有很多 bug). 这种表面整洁还是要尽量避免啊(笑).