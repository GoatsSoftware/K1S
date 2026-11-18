FROM python:3.11@sha256:55c475496e35ad8d898659c85f92b42d3b1c58f25f5d79023baf0840b0b4a462 AS builder

WORKDIR /build
COPY api-gateway/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

WORKDIR /protos
COPY game-service/game.proto leaderboard-service/leaderboard.proto ./
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. game.proto leaderboard.proto


FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY --from=builder /protos/*_pb2*.py ./
COPY api-gateway/gateway.py .

EXPOSE 8080
CMD ["python", "gateway.py"]
