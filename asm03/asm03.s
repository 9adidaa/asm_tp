section .data
    match db "1337", 10
    match_len equ $ - match

section .text
global _start

_start:
    mov rcx, [rsp]
    cmp rcx, 2
    jne bad

    mov rsi, [rsp+16]

    cmp byte [rsi], '4'
    jne bad
    cmp byte [rsi+1], '2'
    jne bad
    cmp byte [rsi+2], 0
    jne bad

    mov eax, 1
    mov edi, 1
    mov rsi, match
    mov edx, match_len
    syscall

    xor edi, edi
    jmp exit

bad:
    mov edi, 1

exit:
    mov eax, 60
    syscall
