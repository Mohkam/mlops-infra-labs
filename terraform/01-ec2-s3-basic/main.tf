resource "aws_instance" "web" {
    ami           = "ami-04a658aa22859f558"
    instance_type = var.instance_type
    key_name      = var.key_name

    tags = {
        Name = "Keonho-Terraform-EC2"
    }
}

resource "aws_s3_bucket" "bucket" {
    bucket = var.bucket_name
    tags = {
        Environment = "Dev"
        Owner       = "Keonho"
    }
}
