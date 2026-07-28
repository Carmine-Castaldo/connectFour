#ifndef CONNECTCONTROLLER_H
#define CONNECTCONTROLLER_H

int init_server(int port);
void accept_connection(int server_socket);
void *handle_client(void *client_server);
int send_msg(int client_socket, char *msg);
int recv_msg(int client_socket, char *buffer);

#endif