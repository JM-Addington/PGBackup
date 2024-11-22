# Rebuilds the docker image and restarts the container

composefile="docker-compose.yml"
tag="pgbackup/prod"
dockerfile="Dockerfile"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -hard)
      hard=true
      shift
      ;;
    -attach)
      echo "Attach flag detected. Attaching to container after rebuild."
      attached=true
      shift
      ;;
    -buildonly)
      echo "Build-only flag detected. The script will only build the image and not start the container."
      buildonly=true
      shift
      ;;
    -help)
      echo "Help flag detected."
      echo "-help         Display this help message"
      echo "-hard         Remove all containers and images before rebuilding, useful for debugging"
      echo "-attach       Attach to container after rebuild"
      echo "-buildonly    Only build the image, do not start the container"
      echo
      help=true
      exit 0
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# See which path to use for docker compose, which is not the same across all iamges
dc1=`which docker-compose`
dc2=`which docker`
if [ -z "$dc1" ] && [ -z "$dc2" ]; then
    echo "Docker-compose or docker not found. Please install docker and docker-compose."
    exit 1
fi

if [ -z $dc1 ]; then
    dc="docker compose"
else
    dc="docker-compose"
fi

if [ "$hard" = true ]; then

  echo "Hard flag detected. Removing all related containers and images."
  sleep 5
  $dc -f "$composefile" down --remove-orphans
  docker image rmi "$tag"
  docker image prune -f
  docker builder prune -a -f

elif [ "$hard" = false ]; then
  $dc -f "$composefile" down
fi

docker build \
  -f "$dockerfile" \
  -t "$tag" .

if [ "$buildonly" = true ]; then
  exit 0
fi

if [ "$attached" = true ]; then
  echo "Attaching to container..."
  $dc -f "$composefile" up
else
  $dc -f "$composefile" up -d
  echo "Bashing you into container..."
  sleep 1
  container=`docker ps|grep "$tag"|awk '{print $1}'` && docker exec -ti "$container" bash
fi