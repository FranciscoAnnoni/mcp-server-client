#!/bin/bash
source .env


function usage {
  echo "Usage: $0 [ -e dev|prod ][ -t <image-tag> ][ -p <aws-profile> ][ -v ] " 1>&2
  echo "Example: $0 -e dev -t v1.0.1 -p shared-services" 1>&2
}

function exit_with_usage {
  usage
  exit 1
}

# CHECK DE LOS ARGUMENTOS QUE LE PASARON
function check_arguments {
  if [ -z $TAG ] || [ -z $AWS_PROFILE ] || [ -z $ENV ]; then
    exit_with_usage
  fi
  if [ "$ENV" != "dev" ] && [ "$ENV" != "prod" ]; then
    exit_with_usage
  fi
  export TAG=$TAG
  export ENV=$ENV
  export REVISION=$(git rev-parse --short HEAD)
  if [ $ENV == "prod" ]; then
     export DOMAIN='rappi.com'
     export ECR_REPO='devex-mcp'
     export ENVIRONMENT='prod'
  else
     export DOMAIN='dev.rappi.com'
     export ECR_REPO='devex-mcp-dev'
     export ENVIRONMENT='dev'
  fi
}

function ecr_login {
  info "Performing ECR login"
  aws ecr get-login-password --region us-west-2 --profile $AWS_PROFILE | docker login --username AWS --password-stdin 060422201113.dkr.ecr.us-west-2.amazonaws.com
  if [ $? != 0 ]; then
    exit 1
  fi
}

function build_and_push {
  info "Building and pushing..."
  docker build -t 060422201113.dkr.ecr.us-west-2.amazonaws.com/${ECR_REPO}:${TAG} .
  docker push 060422201113.dkr.ecr.us-west-2.amazonaws.com/${ECR_REPO}:${TAG} || exit 1
}

function create_deployment_from_template {
  info "Creating deployment from template"
  cat deploy/templates/deployment.yml | envsubst | kubectl apply -f -
}

function info {
  GREEN='\033[0;32m'
  NC='\033[0m' # No Color
  echo -e "${GREEN}[ INFO ]${NC} - $1"
}


while getopts ":e:t:p:v" options; do
  case "${options}" in
    t)
      TAG=${OPTARG}
      ;;
    p)
      AWS_PROFILE=${OPTARG}
      ;;
    e)
      ENV=${OPTARG}
      ;;
    v)
      VERBOSE=true
      ;;
    :)
      echo "Error: -${OPTARG} requires an argument."
      exit_with_usage
      ;;
    *)
      exit_with_usage
      ;;
  esac
done


check_arguments
ecr_login
build_and_push
create_deployment_from_template
kubectl apply -f deploy/resources/$ENV
kubectl rollout restart deployment -n devex-mcp-$ENV
info "Deployment finished. Environment: $ENV Version: ${TAG}"
exit 0