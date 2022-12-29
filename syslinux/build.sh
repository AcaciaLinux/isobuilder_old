docker build --rm --no-cache -t buildtime .
docker run --rm -t -i -v $(pwd)/target:/host/ -it --name debian_isolinux buildtime
