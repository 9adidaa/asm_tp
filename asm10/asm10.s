global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 4
    jl exit_ok

    mov rdi, [rsp+16]
    call atoi
    mov r12, rax

    mov rdi, [rsp+24]
    call atoi
    cmp rax, r12
    jle .keep1
    mov r12, rax
.keep1:

    mov rdi, [rsp+32]
    call atoi
    cmp rax, r12
    jle .keep2
    mov r12, rax
.keep2:

    mov rdi, r12
    call print_int

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

print_int:
    mov rax, rdi
    lea rsi, [buf+31]
    mov byte [rsi], 10
    mov rcx, 1

    cmp rax, 0
    jne .loop
    dec rsi
    mov byte [rsi], '0'
    inc rcx
    jmp .write

.loop:
    xor rdx, rdx
    mov rbx, 10
    div rbx
    add dl, '0'
    dec rsi
    mov [rsi], dl
    inc rcx
    test rax, rax
    jne .loop

.write:
    mov rax, 1
    mov rdi, 1
    mov rdx, rcx
    syscall
    ret

section .bss
buf resb 32
