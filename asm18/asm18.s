global _start

section .data
    send_msg     db "Hello, client!", 10
    send_len     equ $ - send_msg

    timeout_msg  db "Timeout: no response from server", 10
    timeout_len  equ $ - timeout_msg

    prefix       db 'message: "'
    prefix_len   equ $ - prefix
    quote_end    db '"', 10
    quote_len    equ $ - quote_end

    sockaddr:
        dw 2
        dw 0x901f
        dd 0x0100007f
        dq 0

section .bss
    sock    resq 1
    buf     resb 512
    pfd     resb 8          ; struct pollfd

section .text
_start:
    mov eax, 41
    mov edi, 2
    mov esi, 2
    xor edx, edx
    syscall
    test eax, eax
    js exit_fail
    mov [sock], rax

    mov eax, 44
    mov rdi, [sock]
    lea rsi, [rel send_msg]
    mov edx, send_len
    xor r10d, r10d
    lea r8, [rel sockaddr]
    mov r9d, 16
    syscall

    mov eax, [sock]
    mov dword [pfd], eax
    mov word  [pfd+4], 1    ; POLLIN
    mov word  [pfd+6], 0

    mov eax, 7
    lea rdi, [rel pfd]
    mov esi, 1
    mov edx, 5000
    syscall
    test eax, eax
    jle timeout

    test word [pfd+6], 1
    jz timeout

    mov eax, 45
    mov rdi, [sock]
    lea rsi, [rel buf]
    mov edx, 512
    xor r10d, r10d
    xor r8d, r8d
    xor r9d, r9d
    syscall
    test eax, eax
    jle timeout
    mov r15, rax

    mov eax, 1
    mov edi, 1
    lea rsi, [rel prefix]
    mov edx, prefix_len
    syscall

    mov eax, 1
    mov edi, 1
    lea rsi, [rel buf]
    mov rdx, r15
    syscall

    mov eax, 1
    mov edi, 1
    lea rsi, [rel quote_end]
    mov edx, quote_len
    syscall

    jmp exit_ok

timeout:
    mov eax, 1
    mov edi, 1
    lea rsi, [rel timeout_msg]
    mov edx, timeout_len
    syscall

exit_ok:
    mov eax, 60
    xor edi, edi
    syscall

exit_fail:
    mov eax, 60
    mov edi, 1
    syscall
