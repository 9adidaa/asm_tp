global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl exit_ok

    mov rdi, [rsp+16]
    call atoi
    mov r12, rax
    xor rdx, rdx
    mov rbx, 26
    div rbx
    mov r12, rdx

    mov rax, 0
    mov rdi, 0
    mov rsi, buf
    mov rdx, 4096
    syscall
    mov r13, rax
    test r13, r13
    jle exit_ok

    xor rcx, rcx

loop:
    cmp rcx, r13
    jge print

    mov al, [buf+rcx]

    cmp al, 'a'
    jb check_upper
    cmp al, 'z'
    ja check_upper
    sub al, 'a'
    add al, r12b
    mov bl, 26
    xor ah, ah
    div bl
    mov al, ah
    add al, 'a'
    mov [buf+rcx], al
    jmp next

check_upper:
    mov al, [buf+rcx]
    cmp al, 'A'
    jb next
    cmp al, 'Z'
    ja next
    sub al, 'A'
    add al, r12b
    mov bl, 26
    xor ah, ah
    div bl
    mov al, ah
    add al, 'A'
    mov [buf+rcx], al

next:
    inc rcx
    jmp loop

print:
    mov rax, 1
    mov rdi, 1
    mov rsi, buf
    mov rdx, r13
    syscall

exit_ok:
    mov rax, 60
    xor rdi, rdi
    syscall

atoi:
    xor rax, rax
    xor rcx, rcx
.next:
    mov bl, [rdi+rcx]
    cmp bl, 0
    je .done
    sub bl, '0'
    imul rax, rax, 10
    add rax, rbx
    inc rcx
    jmp .next
.done:
    ret

section .bss
buf resb 4096
