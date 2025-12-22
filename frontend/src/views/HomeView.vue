<template>
  <section class="page page-center">
    <div class="card card-lg">
      <h1 class="title">NNTrackBuilder</h1>
      <p class="subtitle">
        Web-интерфейс для управления AI-профилями, задачами и картой.
      </p>
      <div class="actions">
        <RouterLink to="/auth" class="btn primary">Войти / Зарегистрироваться</RouterLink>
        <RouterLink to="/dashboard" class="btn outline">Открыть дашборд</RouterLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import { RouterLink } from 'vue-router'
</script>
