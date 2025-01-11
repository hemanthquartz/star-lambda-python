{
  "StartAt": "CheckPath",
  "States": {
    "CheckPath": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.detail.path",
          "StringContains": "devl1",
          "Next": "SendToSQS"
        }
      ],
      "Default": "NoDevl1Found"
    },
    "SendToSQS": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sqs:sendMessage",
      "Parameters": {
        "QueueUrl": "https://sqs.REGION.amazonaws.com/ACCOUNT_ID/MyQueue",
        "MessageBody.$": "$"
      },
      "End": true
    },
    "NoDevl1Found": {
      "Type": "Fail",
      "Error": "PathError",
      "Cause": "The path does not contain devl1"
    }
  }
}
