---
title: "Parameter Store"
date: 2020-08-25T08:01:20+09:00
tags: [DevOps]
draft: false
---

# Parameter Store

* aws ssm describe-parameters
* aws ssm get-parameters-by-path --path / --recursive
* aws ssm get-parameter --name /dev/tabsrv/passwd
* aws ssm put-parameter --name /prod/tabsrv/server --value 'hoge' --type String
* aws ssm delete-parameter --name /prod/tabsrv/userid
* aws ssm delete-parameters --names /prod/tabsrv /prod/tabsrv/server
	
