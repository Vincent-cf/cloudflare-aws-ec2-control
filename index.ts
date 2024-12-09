import { EC2 } from "@aws-sdk/client-ec2";

interface Env {
  AWS_ACCESS_KEY: string;
  AWS_SECRET_KEY: string;
  INSTANCE_ID: string;
}

export default {
  async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    const awsAccessKey = env.AWS_ACCESS_KEY;
    const awsSecretKey = env.AWS_SECRET_KEY;
    const instanceId = env.INSTANCE_ID;
    const region = "eu-west-1"; // Hardcoded region

    if (!awsAccessKey || !awsSecretKey) {
      return;
    }

    const ec2Client = new EC2({
      region: region,
      credentials: {
        accessKeyId: awsAccessKey,
        secretAccessKey: awsSecretKey,
      },
    });

    try {
      const describeInstancesResult = await ec2Client.describeInstances({ InstanceIds: [instanceId] });
      const currentState = describeInstancesResult.Reservations?.[0]?.Instances?.[0]?.State?.Name;

      if (currentState === "stopped") {
        await ec2Client.startInstances({ InstanceIds: [instanceId] });
      } else if (currentState === "running") {
        await ec2Client.stopInstances({ InstanceIds: [instanceId] });
      }
    } catch (error) {
      console.error("Error managing EC2 instance:", error);
    }
  },
};
