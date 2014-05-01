{% extends "base.tpl" %}
{% block title %}Home{% endblock %}
{% block content %}
  <h2>Datasets by Tag</h2>
  <ul class="nav nav-pills nav-stacked">
    {% for tag in tags %}
      <li><a href="/dataset/tagged?tag={{ tag.name }}">{{ tag.name }} <span class="badge">{{ tag.count }}</span></a></li>
    {% endfor %}
  </ul>
{% endblock %}