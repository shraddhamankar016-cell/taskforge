# OPTIONAL: single EC2 running k3s. NOT free beyond free-tier hours -> run `terraform destroy` after demo.
terraform {
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
}
variable "region"   { default = "ap-south-1" }
variable "key_name" { description = "Existing EC2 key pair" }
provider "aws" { region = var.region }

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_security_group" "k3s" {
  name_prefix = "taskforge-"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # restrict to YOUR_IP/32
  }
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "k3s" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.micro"
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.k3s.id]
  user_data              = "#!/bin/bash\ncurl -sfL https://get.k3s.io | sh -\n"
  tags                   = { Name = "taskforge-k3s" }
}

output "ssh" { value = "ssh -i <key>.pem ubuntu@${aws_instance.k3s.public_ip}" }
