# Containers and orchestration exam plan

*Docker and Kubernetes practical exam*

## Exam overview
The exam lasts for a total of 180 minutes

Build up the complete application for 30 points
Diagnose and repair the kubernetes applications for 70 points

The application follows the Python and PostgreSQL pattern used in the labs. Every student action stays within their assigned namespace.

In the exam it is only allowed to use the following resources and the following resources only.
- https://kubernetes.io/docs/home/
- https://docs.docker.com/
- https://helm.sh/docs/

It is **NOT** allowed to use the resources we already built in the practical labs

| Part | Assessment | Points |
| --- | --- | ---: |
| Part A | Build and operate the application | 30 |
| Part B | Diagnose and repair eleven independent incidents | 70 |
| Total | Individual practical examination | 100 |

## What is provided for you for the exam

The kubernetes environment where you will be working including all of the controllers and 3rd party tools to successfully complete the exam

The teacher provides the postgresql helm chart to be used for the part A of the exam.
Also the annotations for the ingress resource to create an ALB will be provided for you

### What happens before the exam

Since Part A of the exam is basically what we've built together over the 8 weeks then it is not possible to keep it there.
I will remove all of the resources you had built so far in the kubernetes cluster the night before the exam. Also your ECR repositories where you keep the images will be emptied.

## Part A Build the application for 30 points

Goal of part A is to build out an application that covers the following requirements

1. Build a Dockerfile using the best practices of multi-stage images - Points 4
    - [ ] Separate build and runtime stages
    - [ ] Copy only the necessary files into the Dockerfile
    - [ ] non-root runtime user
    - [ ] Listen on a port
2. Publish the application image - Points 2
    - [ ] Build for linux/amd64
    - [ ] Push a semantic version tag to your registry
3. Create the kubernetes resources in your namespace - Points 8
    - [ ] Deployment
    - [ ] Service
    - [ ] Configmap to define shared configuration
    - [ ] Secret for credentials
5. Deploy Postgresql with persistent data - Points 4
6. Configure application health probes - Points 2
7. Expose the application through the AWS ALB by creating an Ingress - Points 2
8. Build the application into a helm chart and install it - Points 6
9. Teacher will ask some final questions based on the provided work - Points 2

### Hints

To get the base template for a kubernetes resources you can either try to find the resources in the kubernetes documentation or use the `--dry-run=client` flag in kubernetes create commands
For example
```
kubectl create deploy web --image test --dry-run=client -o yaml
kubectl create svc clusterip app --tcp=8080:80 --dry-run=client -o yaml
```

### How the grading will be for part A

When you have completed everything you want/know to build call over the teacher and present to them how you have completed each stage
The teacher will review the work and ask some final questions based on how things are built up

## Part B Repair kubernetes incidents

In your namespace you have 11 incidents. Each has its own deployment and you need to get all of them running.
Here you do not need to build docker images
The students will need to get and describe the resources to get the manifests and find the issue
Each incident is given points on how hard I think they are. Fix them all to get max points

| Incident | Total |
| --- | ---: |
| Image issues | 2 |
| Traffic not being served to the pod | 2 |
| Can't find a node for the pod | 2 |
| ??? | 4 |
| ??? | 6 |
| ??? | 6 |
| ??? | 8 |
| ??? | 8 |
| ??? | 10 |
| ??? | 10 |
| ??? | 12 |
| Part B total | 70 |

### Grading

All issues need to be fixed as intended by the teacher.
Deleting a deployment and running a basic busybox image with the same name for example is not permitted and will result in that incident being worth 0 points

If you think you've found the issue but are unsure what is the correct way to fix it then call over the teacher

## How do I practice for the exam?

Part A - Try to build the application we created in the practical labs by yourself. I have outlined the core parts in the Part A description.
  - Note that it is easier to build the application as a kubernetes manifest first and replace some parameters with values but the postgresql database is easier build during the helm build phase using the teacher provided helm chart

Part B - Apply the broken manifests in your own Docker Desktop or managed Kubernetes clusters, find the issue and fix them yourself. The core principals of finding the issue by checking logs and events will stay the same.
  - Note that if you want to build the `broken` manifests on managed kubernetes you will need to point the `image` to your own ECR repo as it will not work on EKS out of the box. It will be fine if you apply it onto your own Docker Desktop Kubernetes.
