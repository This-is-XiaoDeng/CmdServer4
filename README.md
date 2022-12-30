# CmdServer 4

## 简介

远程执行命令

#### 特点

- 轻量：`v4.0.0-pre`版本全项目总计 21.1 KiB (21,639 字节)
- 快速：简单配置后即可建立连接
- 适用广：可直接与无公网IP设备建立连接

#### 文件树（`v4.0.0-pre`）

```
.
├── CmdServer4-Control			// CmdServer主控端
│   └── CmdServer4-Control-Web
│       ├── config.json
│       └── main.py
├── CmdServer4-Controlled		// CmdServer被控端
│   ├── config.json
│   ├── main.py
│   ├── server.py
│   └── update_checker.py
└── CmdServer4-Server			// CmdServer节点服武端
    ├── config.json
    ├── main.py
    └── server.py
```

## 搭建

### 依赖

#### 服务端

1. Python3

#### 主控端

##### Web

1. Python3
2. flask

#### 被控端

1. Python3

### 步骤

1. 安装Python3
2. 选择您的端类型
3. 安装依赖库（仅主控Web端）
4. 修改程序配置（可选）
5. 启动程序

#### 人话：

在被控设备进入`CmdServer4-Controlled/`，运行`python3 main.py`

输出类似以下内容为开启成功，请记住5位客户端ID（`client_id`）

```bash
[21:33:12][server / INFO]: CmdServer started, client id: f4pzm
```
随后在主控设备进入`CmdServer4-Control/`，以`CmdServer4-Control-Web`为例，进入目录，运行`python3 main.py 刚刚拿到的client id`

在浏览器访问`http://127.0.0.1:8081/send?command=命令&cwd=工作目录`即可



