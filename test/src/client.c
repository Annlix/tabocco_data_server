#include <stdio.h>
#include <sys/socket.h>
#include <string.h>
#include <assert.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>

#define MAX_BUF_SIZE 1024 * 10
#define MAX_DIR_LEN 512

extern char * optarg;
extern int optind, opterr, optopt;
enum METHOD {update_time=1, pull_param, push_data, push_data_size, push_image, update_device_info};
typedef struct tcp_args_s {
    char host[15];
    int port;
    enum METHOD method;
} tcp_args_t;
time_t curr;

void get_options(int argc, char * argv[], tcp_args_t * options)
{
    int ch;
    while (-1 != (ch = getopt(argc, argv, "h:p:m:")))
    {
        switch (ch)
        {
        case 'h':
            strncpy(options->host, optarg, 15);
            break;
        case 'p':
            options->port = atoi(optarg);
            break;
        case 'm':
            options->method = atoi(optarg);
            break;
        }
    }
    
}

char * get_request_body(enum METHOD method) 
{
    char * body = calloc(MAX_BUF_SIZE, sizeof (char));
    switch (method)
    {
    case update_time:
        sprintf(body, "{\"method\":\"update_time\"}");
        break;
    case pull_param:
        sprintf(body, "{\"method\":\"pull_param\",\"device_id\": 127}");
        break;
    case push_data:
        sprintf(body, "{\"method\":\"push_data\",\"device_id\":127,\"device_config_id\":251,\"package\":{\"%d\":{\"temp_debug\":3,\"rain_debug\":100},\"%d\":{\"temp_debug\":180,\"rain_debug\":230}}}", curr, curr + 1);
        break;
    case push_data_size:
        sprintf(body, "{\"method\":\"push_data_size\",\"device_id\":79}");
        break;
    case push_image:
        break;
    case update_device_info:
        sprintf(body, "{\"method\":\"update_device_info\"}");
    default:
        break;
    }
    return body;
}

int main(int argc, char * argv[])
{
    tcp_args_t options;
    time(&curr);
    get_options(argc, argv, &options);
    int res, client;
    assert(-1 !=(client = socket(AF_INET, SOCK_STREAM, 0)));
    if (-1 != client) {
        struct sockaddr_in addr;
        addr.sin_family = AF_INET;
        addr.sin_port = htons(options.port);
        addr.sin_addr.s_addr = inet_addr(options.host);
        assert(-1 != (res = connect(client, (struct sockaddr *)&addr, sizeof(addr))));
        if (options.method != push_image) {
            // Get the request data
            char * request_body = calloc(MAX_BUF_SIZE, sizeof(char));
            strncpy(request_body, get_request_body(options.method), MAX_BUF_SIZE);
            puts(">>>>>>");
            printf("[SEND]: %s\n", request_body);
            assert(-1 != (res = send(client, request_body, strlen(request_body) * sizeof(request_body[0]), MSG_NOSIGNAL)));
            char * response = calloc(MAX_BUF_SIZE, sizeof(char));
            int recv_size;
            while(MAX_BUF_SIZE <= (recv_size = recv(client, response, MAX_BUF_SIZE * sizeof(response[0]), MSG_WAITALL)));
            response[recv_size] = '\0';
            puts("<<<<<<");
            printf("[RECV]: %s\n", response);
            puts("Success");
        } else {
            // 1. push image info
            // char * request_body = calloc(MAX_BUF_SIZE, sizeof(char));
            char * cwd = calloc(MAX_DIR_LEN, sizeof(char));
            long file_size; // bytes
            char * request_body = calloc(MAX_BUF_SIZE, sizeof(char));
            getcwd(cwd, MAX_DIR_LEN);
            char * img_path = calloc(MAX_DIR_LEN, sizeof(char));
            sprintf(img_path, "%s/src/test.jpeg", cwd);
            FILE * fp;
            puts(img_path);
            assert(NULL != (fp = fopen(img_path, "rb")));
            fseek(fp, 0L, SEEK_END);
            file_size = ftell(fp);
            rewind(fp);
            sprintf(request_body, "");
            sprintf(request_body, "{\"method\":\"push_image\",\"size\":%ld,\"device_id\":100,\"ts\":%d,\"key\":\"img_key\",\"device_config_id\":2}", file_size, curr);
            puts(">>>>>>");
            printf("[SEND]: %s\n", request_body);
            assert(-1 != (res = send(client, request_body, strlen(request_body) * sizeof(request_body[0]), MSG_NOSIGNAL)));
            printf("DEBUG:%s", request_body);
            sprintf(request_body, "");
            while(MAX_BUF_SIZE == (fread(request_body, sizeof(char), MAX_BUF_SIZE, fp))) {
                assert(-1 != (res = send(client, request_body, strlen(request_body) * sizeof(request_body[0]), MSG_NOSIGNAL)));
            }
            assert(-1 != (res = send(client, request_body, strlen(request_body) * sizeof(request_body[0]), MSG_NOSIGNAL)));
            char * response = calloc(MAX_BUF_SIZE, sizeof(char));
            int recv_size;
            while(MAX_BUF_SIZE <= (recv_size = recv(client, response, MAX_BUF_SIZE * sizeof(response[0]), MSG_WAITALL)));
            response[recv_size] = '\0';
            puts("<<<<<<");
            printf("[RECV]: %s\n", response);
            puts("Success");
        }
    } else {
        fprintf(stderr, "Cannot create a socket.");
    }
}