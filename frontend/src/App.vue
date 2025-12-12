<template>
  <div class="app-root">
    <NavBar />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
</script>