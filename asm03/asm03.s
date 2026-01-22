section .bss
    buf resb 128

section .data
    match db "1337", 10
    match_len equ $ - match

section .text
global _start

_start:
    mov rbx, rsp
    mov rcx, [rbx]        
    cmp rcx, 2
    jne exit

    mov rsi, [rbx + 16]   
    mov rdi, buf

copy_loop:
    mov al, [rsi]
    mov [rdi], al
    inc rsi
    inc rdi
    test al, al
    jne copy_loop

    ; check "42"
    cmp byte [buf], '4'
    jne .no_match
    cmp byte [buf+1], '2'
    jne .no_match
    cmp byte [buf+2], 0
    jne .no_match

    ; print match
    mov rax, 1
    mov rdi, 1
    mov rsi, match
    mov rdx, match_len
    syscall

    xor rdi, rdi
    jmp exit

.no_match:
    mov rdi, 1

exit:
    mov rax, 60
    syscall
