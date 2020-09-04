FROM klakegg/hugo

COPY "src" "/src"
RUN "mkdir /src/public"
WORKDIR "/src"