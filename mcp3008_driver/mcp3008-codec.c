/*
 * mcp3008-codec.c - Codec ASoC virtuel pour l'entrée audio via MCP3008
 *
 * Ce driver lit les données du MCP3008 via SPI et les fournit sous forme
 * d'échantillons PCM 8 bits en mono à 8 kHz.
 *
 * Pour chaque lecture, le driver envoie une commande SPI sur 3 octets,
 * extrait la valeur 10 bits, puis ne conserve que les 8 bits de poids fort 
 * (soit value >> 2). La lecture est déclenchée périodiquement par un hrtimer,
 * afin de respecter la fréquence d'échantillonnage (8 kHz, soit une période de 125 µs).
 */

#include <linux/module.h>
#include <linux/spi/spi.h>
#include <linux/slab.h>
#include <linux/hrtimer.h>
#include <linux/ktime.h>
#include <linux/spinlock.h>
#include <sound/soc.h>
#include <sound/pcm_params.h>

#define BUFFER_SIZE     8192           /* Nombre d'échantillons dans le tampon circulaire */
#define SAMPLE_RATE     8000           /* Fréquence d'échantillonnage en Hz */
#define TIMER_PERIOD_NS 125000ULL      /* Période du timer en nanosecondes (125 µs) */

/* Structure contenant les données internes du codec */
struct mcp3008_codec_data {
    struct spi_device *spi;
    struct hrtimer timer;      /* hrtimer pour déclencher la lecture périodique */
    bool running;              /* Indique si la capture est active */
    u8 *buffer;                /* Tampon circulaire stockant les échantillons 8 bits */
    size_t buffer_size;        /* Taille du tampon (nombre d'échantillons) */
    size_t sample_pos;         /* Position actuelle d'écriture dans le tampon */
    spinlock_t lock;           /* Protection de l'accès au tampon et à sample_pos */
};

/*
 * mcp3008_read_sample() :
 * Effectue une transaction SPI pour lire un échantillon depuis le MCP3008.
 * La commande envoyée (3 octets) configure le MCP3008 en mode single-ended sur le canal 0.
 * La réponse contient la valeur 10 bits, dont on conserve uniquement les 8 bits de poids fort.
 */
static int mcp3008_read_sample(struct mcp3008_codec_data *data)
{
    int ret;
    u8 tx[3] = { 1, (8 << 4), 0 }; /* Bit de start et sélection du canal 0 en mode single-ended */
    u8 rx[3];

    ret = spi_write_then_read(data->spi, tx, 3, rx, 3);
    if (ret < 0)
        return ret;

    /* Extraction de la valeur 10 bits */
    int value = ((rx[1] & 0x03) << 8) | rx[2];
    /* Conserver les 8 bits de poids fort : décale de 2 bits à droite */
    return value >> 2;
}

/*
 * mcp3008_timer_callback() :
 * Fonction appelée par le hrtimer à chaque période (125 µs).
 * Elle lit un échantillon, le stocke dans le tampon circulaire et réarme le timer.
 */
static enum hrtimer_restart mcp3008_timer_callback(struct hrtimer *timer)
{
    struct mcp3008_codec_data *data = container_of(timer, struct mcp3008_codec_data, timer);
    int sample;

    sample = mcp3008_read_sample(data);
    if (sample >= 0) {
        spin_lock(&data->lock);
        data->buffer[data->sample_pos] = (u8)sample;
        data->sample_pos = (data->sample_pos + 1) % data->buffer_size;
        spin_unlock(&data->lock);
    }
    /* Réarme le timer pour la prochaine période */
    hrtimer_forward_now(timer, ns_to_ktime(TIMER_PERIOD_NS));
    return HRTIMER_RESTART;
}

/*
 * Callback hw_params:
 * Vérifie que le format demandé correspond aux contraintes du codec.
 * Seuls 8 kHz, mono et format PCM 8 bits non signé (U8) sont acceptés.
 */
static int mcp3008_codec_hw_params(struct snd_soc_component *component,
                                   struct snd_pcm_substream *substream,
                                   struct snd_pcm_hw_params *params)
{
    if (params_rate(params) != SAMPLE_RATE)
        return -EINVAL;
    if (params_channels(params) != 1)
        return -EINVAL;
    if (params_format(params) != SNDRV_PCM_FORMAT_U8)
        return -EINVAL;
    return 0;
}

/*
 * Callback trigger:
 * Démarre ou arrête la capture audio.
 * Au déclenchement START, on démarre le hrtimer qui lance périodiquement les lectures.
 * Au déclenchement STOP, on annule le timer.
 */
static int mcp3008_codec_trigger(struct snd_soc_component *component,
                                 struct snd_pcm_substream *substream,
                                 int cmd)
{
    struct mcp3008_codec_data *data = snd_soc_component_get_drvdata(component);

    switch (cmd) {
    case SNDRV_PCM_TRIGGER_START:
        if (!data->running) {
            data->running = true;
            hrtimer_start(&data->timer, ns_to_ktime(TIMER_PERIOD_NS), HRTIMER_MODE_REL);
        }
        break;
    case SNDRV_PCM_TRIGGER_STOP:
        if (data->running) {
            hrtimer_cancel(&data->timer);
            data->running = false;
        }
        break;
    default:
        return -EINVAL;
    }
    return 0;
}

/*
 * Callback pointer:
 * Retourne la position actuelle dans le tampon circulaire (en nombre d'échantillons).
 * Cette valeur est utilisée par ALSA pour déterminer la quantité de données capturées.
 */
static snd_pcm_uframes_t mcp3008_codec_pointer(struct snd_soc_component *component,
                                               struct snd_pcm_substream *substream)
{
    struct mcp3008_codec_data *data = snd_soc_component_get_drvdata(component);
    unsigned long pos;
    spin_lock(&data->lock);
    pos = data->sample_pos;
    spin_unlock(&data->lock);
    return pos;
}

/*
 * Structure de composant ASoC du codec.
 * On y associe nos callbacks pour la configuration (hw_params), le déclenchement (trigger)
 * et la lecture de la position (pointer).
 */
static const struct snd_soc_component_driver soc_codec_mcp3008 = {
    .hw_params = mcp3008_codec_hw_params,
    .trigger   = mcp3008_codec_trigger,
    .pointer   = mcp3008_codec_pointer,
};

/*
 * Définition du DAI du codec.
 * Ici, le codec fournit une interface de capture mono à 8 kHz, avec un format PCM U8.
 */
static struct snd_soc_dai_driver mcp3008_dai = {
    .name = "mcp3008-dai",
    .capture = {
         .stream_name = "MCP3008 Capture",
         .channels_min = 1,
         .channels_max = 1,
         .rates = SNDRV_PCM_RATE_8000,
         .formats = SNDRV_PCM_FMTBIT_U8,
    },
    .symmetric_rate = 1,
};

/*
 * mcp3008_codec_probe():
 * Fonction de mise en service du driver SPI.
 * On y alloue la structure interne, initialise le tampon, le spinlock et le hrtimer,
 * puis on enregistre le composant ASoC auprès du noyau.
 */
static int mcp3008_codec_probe(struct spi_device *spi)
{
    struct mcp3008_codec_data *data;
    int ret;

    data = devm_kzalloc(&spi->dev, sizeof(*data), GFP_KERNEL);
    if (!data)
        return -ENOMEM;

    data->spi = spi;
    data->buffer_size = BUFFER_SIZE;
    data->buffer = devm_kzalloc(&spi->dev, sizeof(u8) * BUFFER_SIZE, GFP_KERNEL);
    if (!data->buffer)
        return -ENOMEM;

    data->sample_pos = 0;
    spin_lock_init(&data->lock);
    data->running = false;

    /* Initialisation du hrtimer en mode relatif */
    hrtimer_init(&data->timer, CLOCK_MONOTONIC, HRTIMER_MODE_REL);
    data->timer.function = mcp3008_timer_callback;

    spi_set_drvdata(spi, data);

    ret = devm_snd_soc_register_component(&spi->dev,
                                            &soc_codec_mcp3008,
                                            &mcp3008_dai, 1);
    if (ret) {
        dev_err(&spi->dev, "Erreur lors de l'enregistrement du codec: %d\n", ret);
        return ret;
    }
    dev_info(&spi->dev, "Codec MCP3008 enregistré avec succès\n");
    return 0;
}

/*
 * mcp3008_codec_remove():
 * Fonction appelée lors du retrait du module.
 * Ici, nous utilisons une fonction de type void.
 */
static void mcp3008_codec_remove(struct spi_device *spi)
{
    /* Les ressources allouées via devm_* seront libérées automatiquement */
}

static const struct of_device_id mcp3008_codec_of_match[] = {
    { .compatible = "custom,mcp3008-codec", },
    { },
};
MODULE_DEVICE_TABLE(of, mcp3008_codec_of_match);

static struct spi_driver mcp3008_codec_driver = {
    .driver = {
        .name = "mcp3008-codec",
        .of_match_table = mcp3008_codec_of_match,
    },
    .probe = mcp3008_codec_probe,
    .remove = mcp3008_codec_remove,
};

module_spi_driver(mcp3008_codec_driver);

MODULE_DESCRIPTION("Codec ASoC virtuel pour MCP3008 (8-bit, 8 kHz) avec hrtimer");
MODULE_AUTHOR("SEIDEL");
MODULE_LICENSE("GPL");
