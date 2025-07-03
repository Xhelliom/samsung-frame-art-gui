# Configuration SmartThings pour Samsung Frame TV

Ce guide explique comment configurer SmartThings comme méthode de fallback pour contrôler votre Samsung Frame TV de 2019.

## Pourquoi SmartThings ?

L'API directe Samsung peut parfois échouer ou être instable. SmartThings offre une alternative plus fiable via le cloud Samsung pour certaines fonctionnalités :
- Contrôle de base de la TV (marche/arrêt, changement de source)
- Vérification du statut de la TV
- Activation du mode Art

⚠️ **Limitation importante** : SmartThings ne permet pas l'upload d'images personnalisées. Cette fonctionnalité nécessite l'API directe.

## Configuration

### 1. Créer un Personal Access Token (PAT)

1. Allez sur https://account.smartthings.com/tokens
2. Connectez-vous avec votre compte Samsung
3. Cliquez sur "Generate new token"
4. Donnez un nom à votre token (ex: "Frame TV Control")
5. Sélectionnez les scopes suivants :
   - `r:devices:*` (lecture des appareils)
   - `x:devices:*` (contrôle des appareils)
6. Copiez le token généré

### 2. Configurer le fichier .env

Ajoutez ces lignes à votre fichier `.env` :

```env
SMARTTHINGS_TOKEN=your_personal_access_token_here
SMARTTHINGS_DEVICE_ID=your_device_id_here
```

### 3. Trouver l'ID de votre TV (optionnel)

Le système peut détecter automatiquement votre TV Frame, mais vous pouvez aussi spécifier l'ID manuellement :

1. Avec le token configuré, vous pouvez tester l'API :
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        https://api.smartthings.com/v1/devices
   ```

2. Recherchez votre TV dans la liste retournée
3. Copiez le `deviceId` et ajoutez-le à votre `.env`

### 4. Vérifier la configuration

Après configuration, redémarrez votre serveur backend. Les logs montreront quelle méthode est utilisée :

- `"Art Mode supporté (méthode directe)"` = API directe fonctionne
- `"Art Mode supporté (SmartThings)"` = Fallback SmartThings utilisé

## Fonctionnalités supportées

### API Directe (prioritaire)
- ✅ Upload d'images personnalisées
- ✅ Sélection d'images
- ✅ Récupération de l'image actuelle
- ✅ Contrôle complet de la TV

### SmartThings (fallback)
- ✅ Activation du mode Art
- ✅ Contrôle de base (marche/arrêt)
- ✅ Envoi de commandes à la TV
- ✅ Récupération du statut
- ❌ Upload d'images personnalisées

## Dépannage

### Token invalide
- Vérifiez que le token est correct
- Assurez-vous que les scopes sont bien configurés
- Le token peut expirer, générez-en un nouveau

### TV non détectée
- Vérifiez que votre TV est bien connectée à SmartThings
- Utilisez l'app SmartThings sur votre téléphone pour vérifier
- Spécifiez manuellement le `SMARTTHINGS_DEVICE_ID`

### Aucune méthode ne fonctionne
- Vérifiez l'adresse IP de votre TV
- Assurez-vous que la TV est allumée
- Vérifiez votre réseau local

## Exemple de configuration complète

```env
# Configuration de base
TV_IP=192.168.1.100
UNSPLASH_ACCESS_KEY=your_unsplash_key

# Configuration SmartThings
SMARTTHINGS_TOKEN=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
SMARTTHINGS_DEVICE_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Le système essaiera automatiquement l'API directe en premier, puis SmartThings en cas d'échec. 