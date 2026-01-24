global _start

section .text
_start:
    mov rax, [rsp]
    cmp rax, 2
    jl exit_ok

    mov rsi, [rsp+16]
    mov al, byte [rsi]
    cmp al, '-'
    jne hex_mode

    mov al, byte [rsi+1]
    cmp al, 'b'
    jne hex_mode

    mov rax, [rsp]
    cmp rax, 3
    jl exit_ok
    mov rdi, [rsp+24]
    call atoi
    mov rdi, rax
    call print_bin
    jmp exit_ok

hex_mode:
    mov rdi, [rsp+16]
    call atoi
    mov rdi, rax
    call print_hex
    jmp exit_ok

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

print_hex:
    mov rax, rdi
    lea rsi, [buf+63]
    mov byte [rsi], 10
    mov rcx, 1
    mov rbx, 16

    cmp rax, 0
    jne .loop
    dec rsi
    mov byte [rsi], '0'
    inc rcx
    jmp .write

.loop:
    xor rdx, rdx
    div rbx
    mov dl, dl
    cmp dl, 9
    jle .digit
    add dl, 55
    jmp .store
.digit:
    add dl, '0'
.store:
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

print_bin:
    mov rax, rdi
    lea rsi, [buf+63]
    mov byte [rsi], 10
    mov rcx, 1
    mov rbx, 2

    cmp rax, 0
    jne .loop
    dec rsi
    mov byte [rsi], '0'
    inc rcx
    jmp .write

.loop:
    xor rdx, rdx
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
buf resb 64
