#!/bin/bash
set -eo pipefail
STACK=monitor-tennis
if [[ $# -eq 1 ]] ; then
    STACK=$1
    echo "Deleting stack $STACK"
fi
FUNCTION=$(aws cloudformation describe-stack-resource --stack-name $STACK --logical-resource-id function --query 'StackResourceDetail.PhysicalResourceId' --output text)
aws cloudformation delete-stack --stack-name $STACK
echo "Deleted $STACK stack."
if [ -f bucket-name.txt ]; then
    ARTIFACT_BUCKET=$(cat bucket-name.txt)
    if [[ ! $ARTIFACT_BUCKET =~ lambda-artifacts-[a-z0-9]{16} ]] ; then
        echo "Bucket was not created by this application. Skipping."
    else
        aws s3 rb --force s3://$ARTIFACT_BUCKET; rm bucket-name.txt
    fi
fi

aws logs delete-log-group --log-group-name /aws/lambda/$FUNCTION

rm -f out.yml out.json function/*.pyc
rm -rf package function/__pycache__
