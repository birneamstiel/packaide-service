FROM cgal/testsuite-docker:ubuntu-cxx11

RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
# TODO shouldn't be necessary but included cgal installation was not found
RUN apt-get install -y libcgal-dev
# TODO for debugging only
RUN apt-get install -y nano

WORKDIR /packaide
COPY . .
WORKDIR /packaide/Packaide
RUN pwd
RUN ls

# Install packaide (together with dependencies)
RUN python3 -m pip install --user . -r requirements.txt

WORKDIR ..
RUN python3 -m pip install -r requirements.txt

CMD ["waitress-serve", "--call CoreApi:create_app"]
# ENTRYPOINT [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]


# ARG dockerfile_url
# ENV DOCKERFILE_URL=$dockerfile_url

# ENV CGAL_TEST_PLATFORM="Ubuntu-Latest-CXX11"
# ENV CGAL_CMAKE_FLAGS="(\"-DCGAL_CXX_FLAGS=-std=c++11 -fext-numeric-literals\" \"-DWITH_CGAL_Qt3:BOOL=OFF\")"
# ENV INIT_FILE=/tmp/init.cmake
# COPY init.cmake /tmp/init.cmake