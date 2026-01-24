global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl exit_ok

    mov rdi, [rsp+16]
    call atoi
    mov rbx, rax

    cmp rbx, 1
    jle print_zero

    dec rbx
    mov rax, rbx
    inc rbx
    imul rax, rbx
    shr rax, 1
    jmp print_result

print_zero:
    xor rax, rax

print_result:
    mov rdi, rax
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
