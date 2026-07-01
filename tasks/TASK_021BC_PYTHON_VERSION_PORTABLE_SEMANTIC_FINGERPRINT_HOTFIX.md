# TASK_021BC Python版本便携语义摘要热修复

## 根因

`ast.dump(..., include_attributes=False)`的默认文本不是跨Python版本稳定协议。空模块可能被显示为`Module()`或`Module(body=[], type_ignores=[])`，因此纯注释文件也会产生不同哈希。

## 修复

改用`PYTHON_TOKEN_STREAM_V1`，排除注释和非语义空行，保留缩进、名称、常量、运算符、字符串和控制流Token。

```text
业务源文件修改：0
业务逻辑修改：false
数据库写操作：0
Git提交允许：false
GitHub推送允许：false
```
