import json
import boto3

cp = boto3.client("codepipeline")
s3 = boto3.resource("s3")

def lambda_handler(event, context):
    print('Begin S3 cleanup')

    try:
      job_id = event["CodePipeline.job"]["id"]
      parameter_raw = event["CodePipeline.job"]["data"]["actionConfiguration"]["configuration"]["UserParameters"]
      parameter_obj = json.loads(parameter_raw)
      target_bucket = parameter_obj["BucketName"]
      print(f"TargetBucket: {target_bucket}")

      # デプロイ先バケットの全ファイルを削除
      res = s3.Bucket("memo.nyamonote.tk").objects.delete()
      if len(res) == 0:
        print("Succeeded cleanup. Target S3 Bucket is empty.")
      elif "Errors" not in res[0]:
        print("Succeeded cleanup. Delete all objects in target S3 bucket.")
      else:
        raise Exception(
          "Error cleanup. Fail delete object in target S3 bucket.", res[0]["Errors"])
      
      # 処理結果を送信
      cp.put_job_success_result(jobId=job_id)

    except Exception as e:
      msg = f"S3 ({target_bucket}) のオブジェクト削除に失敗しました。\nException: {e}"
      print(msg)
      cp.put_job_failure_result(jobId=job_id, failureDetails={ "type": "JobFailed", "message": msg })
      raise

    print('Complete S3 cleanup')
